from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from .types import SegmentDict, TranscriptionResult
from .utils import debug_log

# --- Tuning parameters (easy to adjust later) ---
# Silence trim parameters operate on 16 kHz mono arrays
TRIM_RMS_THRESHOLD: float = 0.012  # RMS threshold for speech vs. silence
TRIM_MIN_VOICED_SEC: float = 0.5  # Require at least this much voiced audio to transcribe
TRIM_PAD_MS: int = 50  # Keep a short pad around detected speech (ms)

# Whisper inference behavior on low/empty audio
WHISPER_NO_SPEECH_THRESHOLD: float = 0.7
WHISPER_CONDITION_ON_PREV: bool = False


class WhisperEngine:
    def __init__(
        self,
        model_name: str,
        translate: bool,
        language: str | None,
        native_segmentation: bool,
        session_dir: Path,
        samplerate: int,
        channels: int,
        verbose: bool = False,
        profile: dict | None = None,
    ) -> None:
        self.model_name = model_name
        self.translate = translate
        self.language = language
        self.native_segmentation = native_segmentation
        self.session_dir = session_dir
        self.samplerate = samplerate
        self.channels = channels
        self.verbose = verbose
        # Use the provided profile dict even if it's empty.
        # Using `or {}` would create a new dict when an empty one is passed,
        # breaking shared accumulation with the caller (CLI).
        self.profile = profile if profile is not None else {}
        self._executor: ThreadPoolExecutor | None = None

    def preload(self) -> tuple[ThreadPoolExecutor | None, Future | None]:
        try:
            self._executor = ThreadPoolExecutor(max_workers=1)

            def _load(name: str):
                import whisper

                t0 = time.perf_counter()
                m = whisper.load_model(name)
                t1 = time.perf_counter()
                return m, (t1 - t0)

            fut = self._executor.submit(_load, self.model_name)
            debug_log(self.verbose, "whisper", f"Submitted model preload: {self.model_name}")
            return self._executor, fut
        except Exception:
            return None, None

    def resolve_model(self, fut: Future | None):
        import whisper

        model = None
        if fut is not None:
            try:
                model, load_dur = fut.result()
                self.profile["model_load_sec"] = self.profile.get("model_load_sec", 0.0) + float(
                    load_dur
                )
                debug_log(
                    self.verbose, "whisper", f"Model resolved via preload in {float(load_dur):.3f}s"
                )
            except Exception:
                model = None
        if model is None:
            t0m = time.perf_counter()
            model = whisper.load_model(self.model_name)
            t1m = time.perf_counter()
            self.profile["model_load_sec"] = self.profile.get("model_load_sec", 0.0) + (t1m - t0m)
            debug_log(self.verbose, "whisper", f"Loaded model synchronously in {(t1m - t0m):.3f}s")
        return model

    def transcribe_chunk(
        self,
        model,
        audio_path: Path,
        frames: int,
        initial_prompt: str | None = None,
    ) -> TranscriptionResult:
        # Load audio without ffmpeg by reading via soundfile and passing a numpy array
        # to Whisper. Convert to mono float32 and resample to 16 kHz as expected by Whisper's API.
        task = "translate" if self.translate else "transcribe"
        try:
            import soundfile as sf
        except Exception as e:
            raise RuntimeError("soundfile is required to read recorded audio.") from e

        from .utils import resample_linear

        # Read audio from file (supports WAV/FLAC via libsndfile), convert to mono
        data, sr = sf.read(str(audio_path), dtype="float32", always_2d=True)
        # data shape: (n_frames, n_channels). Convert to mono by averaging if needed
        if data.ndim == 2 and data.shape[1] > 1:
            mono = data.mean(axis=1)
        else:
            mono = data.reshape(-1)
        # Resample to 16k expected by Whisper when passing arrays
        mono_16k: np.ndarray = resample_linear(mono, int(sr), 16000)

        # Trim leading/trailing silence to avoid hallucinations on near-empty chunks
        def _moving_rms(x: np.ndarray, win_len: int) -> np.ndarray:
            if x.size == 0:
                return np.zeros(0, dtype=np.float32)
            win = np.ones(win_len, dtype=np.float32) / float(win_len)
            sq = np.square(x.astype(np.float32, copy=False))
            # same-length RMS via 'same' convolution
            ma = np.convolve(sq, win, mode="same")
            return np.sqrt(ma).astype(np.float32, copy=False)

        def _trim_silence(x: np.ndarray, sr16k: int) -> tuple[np.ndarray, float, float]:
            # Returns (trimmed, leading_sec, trailing_sec)
            if x.size == 0:
                return x, 0.0, 0.0
            win_len = max(1, int(round(sr16k * 0.03)))  # 30 ms window
            rms = _moving_rms(x, win_len)
            thr = float(TRIM_RMS_THRESHOLD)
            voiced = np.where(rms >= thr)[0]
            if voiced.size == 0:
                return np.zeros(0, dtype=np.float32), 0.0, float(x.size) / sr16k
            start_idx = int(voiced[0])
            end_idx = int(voiced[-1])
            pad = int(round((TRIM_PAD_MS / 1000.0) * sr16k))
            a = max(0, start_idx - pad)
            b = min(x.size, end_idx + pad + 1)
            lead_sec = float(a) / sr16k
            trail_sec = float(x.size - b) / sr16k
            return x[a:b], lead_sec, trail_sec

        pre_sec = float(mono_16k.size) / 16000.0
        trimmed, lead_sec, trail_sec = _trim_silence(mono_16k, 16000)
        post_sec = float(trimmed.size) / 16000.0
        debug_log(
            self.verbose,
            "whisper",
            f"Chunk {audio_path.name}: trim {pre_sec:.2f}s -> {post_sec:.2f}s (lead {lead_sec:.2f}s, tail {trail_sec:.2f}s)",
        )

        # If too short after trimming, skip transcription
        if post_sec < float(TRIM_MIN_VOICED_SEC):
            debug_log(
                self.verbose,
                "whisper",
                f"Chunk {audio_path.name}: too short after trim ({post_sec:.2f}s) – skipping",
            )
            return {"text": "", "segments": []}

        t0 = time.perf_counter()
        debug_log(
            self.verbose, "whisper", f"Transcribing chunk {audio_path.name} (frames={frames})"
        )
        res: dict[str, Any] = model.transcribe(
            trimmed,
            task=task,
            language=self.language,
            fp16=False,
            initial_prompt=(initial_prompt if post_sec >= float(TRIM_MIN_VOICED_SEC) else None),
            condition_on_previous_text=bool(WHISPER_CONDITION_ON_PREV),
            no_speech_threshold=float(WHISPER_NO_SPEECH_THRESHOLD),
        )
        t1 = time.perf_counter()
        self.profile["transcribe_sec"] = self.profile.get("transcribe_sec", 0.0) + (t1 - t0)
        debug_log(
            self.verbose, "whisper", f"Transcribed chunk {audio_path.name} in {(t1 - t0):.3f}s"
        )
        text_c = str(res.get("text", "") or "").strip()
        lang_code = str(res.get("language", "") or "")
        if self.native_segmentation:
            segs_raw = res.get("segments", []) or []
            segs_typed: list[SegmentDict] = []
            for s in segs_raw:
                try:
                    # Adjust for leading trim so times align with original chunk timeline
                    start = float(s.get("start", 0.0)) + float(lead_sec)
                    end = float(s.get("end", 0.0)) + float(lead_sec)
                    text = str(s.get("text", "") or "")
                    segs_typed.append({"start": start, "end": end, "text": text})
                except Exception:
                    continue
            out: TranscriptionResult = {"text": text_c, "segments": segs_typed}
            if lang_code:
                out["language"] = lang_code
            return out
        # Collapsed single segment per chunk
        segs_raw = res.get("segments", []) or []
        start = (float(segs_raw[0].get("start", 0.0)) + float(lead_sec)) if segs_raw else 0.0
        end = (
            (float(segs_raw[-1].get("end", 0.0)) + float(lead_sec))
            if segs_raw
            else (frames / float(self.samplerate))
        )
        out2: TranscriptionResult = {
            "text": text_c,
            "segments": ([{"start": start, "end": end, "text": text_c}] if text_c else []),
        }
        if lang_code:
            out2["language"] = lang_code
        return out2

    def write_chunk_outputs(self, result: TranscriptionResult, audio_path: Path) -> None:
        try:
            from whisper.utils import get_writer

            debug_log(self.verbose, "whisper", f"Writing outputs for {audio_path.name}")
            for fmt in ("txt", "srt", "vtt", "tsv", "json"):
                writer = get_writer(fmt, str(self.session_dir))
                writer(result, str(audio_path))
            debug_log(self.verbose, "whisper", f"Wrote outputs for {audio_path.name}")
        except Exception as e:
            debug_log(
                self.verbose,
                "whisper",
                f"Warning: failed to write chunk outputs for {audio_path.name}: {e}",
            )

    def merge_results(
        self, results: list[TranscriptionResult], offsets: list[float], cumulative_text: str
    ) -> TranscriptionResult:
        merged: TranscriptionResult = {"text": "", "segments": []}
        for res, off in zip(results, offsets, strict=False):
            merged["text"] += res.get("text") or ""
            for s in res.get("segments", []):
                s2: SegmentDict = {}
                if "start" in s:
                    s2["start"] = float(s["start"]) + off
                if "end" in s:
                    s2["end"] = float(s["end"]) + off
                if "text" in s:
                    s2["text"] = s["text"]
                merged["segments"].append(s2)
        if (cumulative_text or "").strip():
            merged["text"] = cumulative_text
        return merged
