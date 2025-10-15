#!/usr/bin/env python3
"""
Interactive microphone recording -> Whisper transcription -> outputs + clipboard

Features
- Records from the default microphone until you press Enter.
- Default recording format is FLAC (lossless); WAV and MP3 are supported. MP3 requires ffmpeg; otherwise it falls back to FLAC with a warning.
- Uses Whisper's Python API (no subprocess) to transcribe/translate and emits txt, srt, vtt, tsv, json.
- Copies the .txt transcript to the system clipboard.
- Creates a per-session subdirectory under a base output directory, named with an ISO timestamp (e.g., 2025-01-31T14-22-05+0200).

Requirements
- Python packages: sounddevice, soundfile, openai-whisper (pip install sounddevice soundfile openai-whisper)
- Optional: ffmpeg (only needed for MP3 or if Whisper loads audio by path for MP3)

Usage
  s2t
Optional
  s2t -l de -m turbo -o transcripts -t -f flac

Notes
- Default output directory is `transcripts/` if `-o/--outdir` is omitted.
- In prompt mode (`-p/--prompt`), speak your prompt first, then press SPACE. The app waits until the prompt is transcribed, prints a separator, and then you start speaking your main content. You may also press ENTER instead of SPACE to finish after the prompt; in that case the session ends after transcribing the prompt.
"""

from __future__ import annotations

import argparse
import json
import logging
import queue
import re
import shutil
import sys
import threading
import time
from pathlib import Path

from . import __version__
from .config import SessionOptions
from .outputs import concat_audio, write_final_outputs
from .recorder import Recorder
from .translator.argos_backend import (
    ArgosTranslator,
    ensure_packages_background,
    translate_result_segments,
)
from .types import TranscriptionResult
from .utils import (
    convert_wav_to_mp3,
    copy_to_clipboard,
    make_session_dir,
    open_in_shell_editor,
)
from .whisper_engine import WhisperEngine


def run_session(opts: SessionOptions) -> int:
    session_dir = make_session_dir(opts.outdir)
    profile_data: dict = {}
    requested = opts.recording_format.lower()
    effective = requested
    if requested == "mp3" and shutil.which("ffmpeg") is None:
        logging.warning("ffmpeg not found; falling back to FLAC recording instead of MP3.")
        effective = "flac"
    ext = ".flac" if effective == "flac" else ".wav"

    engine = WhisperEngine(
        model_name=opts.model,
        translate=False,  # translation handled as post-processing
        language=opts.lang,
        native_segmentation=opts.native_segmentation,
        session_dir=session_dir,
        samplerate=opts.rate,
        channels=opts.channels,
        verbose=opts.verbose,
        profile=profile_data if opts.profile else {},
    )
    ex, fut = engine.preload()

    # Determine translation target languages from options
    target_langs: list[str] = []
    if opts.translate_to:
        target_langs = list(dict.fromkeys([s.strip().lower() for s in opts.translate_to if s]))
    elif opts.translate:
        target_langs = ["en"]

    # Background auto-install/update Argos packages as early as possible
    detected_lang: dict[str, str | None] = {"code": None}
    detected_lang_event = threading.Event()
    translator: ArgosTranslator | None = None
    if target_langs:
        translator = ArgosTranslator(verbose=opts.verbose)
        ensure_packages_background(
            translator,
            src_lang_hint=(opts.lang.lower() if opts.lang else None),
            target_langs=target_langs,
            detected_lang_event=detected_lang_event,
            detected_lang_holder=detected_lang,
        )

    tx_q: queue.Queue[tuple[int, Path, int, float]] = queue.Queue()
    cumulative_text = ""
    next_to_emit = 1
    pending: dict[int, str] = {}
    results: list[TranscriptionResult] = []
    offsets: list[float] = []
    agg_lock = threading.Lock()
    tx_done = threading.Event()

    def _build_latest_ready_prompt(
        current_index: int, finished: dict[int, str], max_chars: int = 800, max_chunks: int = 3
    ) -> str | None:
        parts: list[str] = []
        total = 0
        taken_chunks = 0
        # Walk backward from previous indices
        for idx in range(current_index - 1, 0, -1):
            if idx not in finished:
                continue
            text = finished[idx].strip()
            if not text:
                continue
            # Split into sentences (simple heuristic: ., !, ? followed by whitespace or end)
            sentences = re.split(r"(?<=[.!?])[\s\n]+", text)
            # Take completed sentences from the end
            for s in reversed(sentences):
                s = s.strip()
                if not s:
                    continue
                # Ensure it looks like a completed sentence
                # Use triple-quoted raw string to safely include quotes in the class
                if not re.search(r"""[.!?][\)\]\}"']*$|[.!?]$""", s):
                    # skip likely incomplete trailing fragment
                    continue
                if total + len(s) + (1 if parts else 0) > max_chars:
                    return (" ".join(reversed(parts))) or None
                parts.append(s)
                total += len(s) + (1 if parts else 0)
                # We don't count sentences per chunk strictly, but stop if we already got from enough chunks
            taken_chunks += 1
            if taken_chunks >= max_chunks or total >= max_chars:
                break
        return (" ".join(reversed(parts))) or None

    # Event signaling that prompt (chunk #1) is fully transcribed
    prompt_done = threading.Event()

    def tx_worker():
        model = engine.resolve_model(fut)
        nonlocal cumulative_text, next_to_emit
        finished_texts: dict[int, str] = {}
        while True:
            idx, path, frames, offset = tx_q.get()
            if idx == -1:
                break
            # If in spoken-prompt mode, ensure we don't process payload chunks before prompt is done
            if opts.prompt and idx > 1 and not prompt_done.is_set():
                prompt_done.wait()
            # Build latest-ready prompt based on already finished chunks
            prompt = _build_latest_ready_prompt(idx, finished_texts)
            res = engine.transcribe_chunk(model, path, frames, initial_prompt=prompt)
            # Record detected language once (for translator preload if needed)
            if target_langs and detected_lang["code"] is None:
                lang_code = str(res.get("language") or "").strip().lower()
                if lang_code:
                    detected_lang["code"] = lang_code
                    detected_lang_event.set()
            engine.write_chunk_outputs(res, path)
            text_i = (res.get("text", "") or "").strip()
            with agg_lock:
                if text_i:
                    finished_texts[idx] = text_i
                results.append(res)
                offsets.append(offset)
                pending[idx] = text_i
                while next_to_emit in pending:
                    out = pending.pop(next_to_emit)
                    if out:
                        print(out)
                        print("")
                        cumulative_text += out if not cumulative_text else ("\n\n" + out)
                        try:
                            copy_to_clipboard(cumulative_text)
                        except Exception:
                            pass
                    next_to_emit += 1
                # If this was the prompt chunk, signal readiness and instruct user
                if opts.prompt and idx == 1 and not prompt_done.is_set():
                    prompt_done.set()
                    print("=" * 60)
                    print("Prompt transcribed. Start speaking your main content now.")
                    print("=" * 60)
                    # Allow recorder to resume writing the next chunk
                    if prompt_resume_event is not None:
                        prompt_resume_event.set()
        tx_done.set()

    tx_t = threading.Thread(target=tx_worker, daemon=True)
    tx_t.start()

    if opts.prompt:
        print("Prompt mode enabled: Speak your prompt first, then press SPACE.")
        print("Recording will wait for the prompt transcription before starting payload.")
    # Prepare resume event to pause recording between prompt and payload
    prompt_resume_event = threading.Event() if opts.prompt else None
    rec = Recorder(
        session_dir,
        opts.rate,
        opts.channels,
        ext,
        debounce_ms=opts.debounce_ms,
        verbose=opts.verbose,
        pause_after_first_chunk=opts.prompt,
        resume_event=prompt_resume_event,
        silence_sec=opts.silence_sec,
        min_chunk_sec=opts.min_chunk_sec,
    )
    t0 = time.perf_counter()
    chunk_paths, chunk_frames, chunk_offsets = rec.run(tx_q)
    t1 = time.perf_counter()
    if opts.profile:
        profile_data["recording_sec"] = t1 - t0
    tx_t.join()

    merged: TranscriptionResult = engine.merge_results(results, chunk_offsets, cumulative_text)
    base_audio_path = session_dir / f"recording{ext}"
    txt_path = write_final_outputs(merged, session_dir, base_audio_path)

    try:
        if chunk_paths:
            concat_audio(chunk_paths, base_audio_path, opts.rate, opts.channels)
            if opts.verbose:
                print(f"Merged audio written: {base_audio_path.name}", file=sys.stderr)
            if requested == "mp3" and shutil.which("ffmpeg") is not None:
                mp3_out = session_dir / "recording.mp3"
                convert_wav_to_mp3(
                    (
                        base_audio_path
                        if base_audio_path.suffix.lower() == ".wav"
                        else base_audio_path
                    ),
                    mp3_out,
                )
                if opts.verbose:
                    print(f"Converted merged audio to MP3: {mp3_out.name}", file=sys.stderr)
    except Exception as e:
        if opts.verbose:
            print(f"Warning: failed to merge chunk audio: {e}", file=sys.stderr)

    # Optionally delete chunk files (audio + per-chunk outputs)
    if chunk_paths and not opts.keep_chunks:
        for p in chunk_paths:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
            stem = p.with_suffix("")
            for suf in (".txt", ".srt", ".vtt", ".tsv", ".json"):
                try:
                    (stem.with_suffix(suf)).unlink(missing_ok=True)
                except Exception:
                    pass

    text_final: str = merged.get("text") or cumulative_text
    t_cb0 = time.perf_counter()
    copy_to_clipboard(text_final)
    t_cb1 = time.perf_counter()
    profile_data["clipboard_sec"] = t_cb1 - t_cb0

    print("—" * 60)
    print(f"Done. Files in folder: {session_dir}")
    print("Created:")
    if chunk_paths:
        print(f"  - chunks: {chunk_paths[0].name} … {chunk_paths[-1].name} (x{len(chunk_paths)})")
    print("  - Whisper outputs: .txt, .srt, .vtt, .tsv, .json")
    print(f"Copied TXT to clipboard: {txt_path.name}")

    if opts.edit:
        opened, used = open_in_shell_editor(txt_path)
        if opened:
            print("—" * 60)
            print(f"Opened transcript in editor: {used or '$VISUAL/$EDITOR'}")
        else:
            print("—" * 60)
            print(
                "Could not open an editor from $VISUAL/$EDITOR or fallbacks; printing transcript instead:"
            )
            print(text_final.rstrip("\n"))
    else:
        print("—" * 60)
        print("Transcript (clipboard text):")
        # Visual separator before the actual transcript text
        print("=" * 60)
        print(text_final.rstrip("\n"))

    # Post-processing: translate outputs for requested target languages
    if target_langs and translator is not None:
        # Decide source language: CLI hint takes precedence; else detected; else skip with warning
        src_lang = (opts.lang.lower() if opts.lang else (detected_lang["code"] or "")).strip()
        if not src_lang:
            if opts.verbose:
                print(
                    "Warning: Could not determine source language for translation; skipping post-translation.",
                    file=sys.stderr,
                )
        else:
            # Skip identical language targets
            effective_targets = [t for t in target_langs if t.lower() != src_lang.lower()]
            # Ensure required packages if missing; perform synchronous install as needed
            for tgt in effective_targets:
                if not translator.has_package(src_lang, tgt):
                    print(
                        f"Ensuring Argos translation package for '{src_lang}->{tgt}' (may download 50–250 MB)…",
                        file=sys.stderr,
                    )
                    ok = False
                    try:
                        ok = translator.ensure_package(src_lang, tgt)
                    except Exception as e:
                        print(
                            f"Warning: could not install '{src_lang}->{tgt}' package: {e}",
                            file=sys.stderr,
                        )
                    if not ok and not translator.has_package(src_lang, tgt):
                        print(
                            f"Warning: translation package unavailable or failed for '{src_lang}->{tgt}'. Skipping.",
                            file=sys.stderr,
                        )
                        continue
            try:
                translated = translate_result_segments(translator, merged, src_lang, tgt)
                # Write translated outputs with language suffix by passing a suffixed base path
                suffixed = base_audio_path.with_name(
                    f"{base_audio_path.stem}.{tgt}{base_audio_path.suffix}"
                )
                write_final_outputs(translated, session_dir, suffixed)
                if opts.verbose:
                    print(f"Created translated outputs for '{tgt}'.", file=sys.stderr)
            except Exception as e:
                print(
                    f"Warning: failed to translate to '{tgt}': {e}",
                    file=sys.stderr,
                )

    if opts.profile:
        try:
            prof_path = session_dir / "profile.json"
            prof_json = {**profile_data}
            prof_json["total_sec"] = prof_json.get("total_sec", (time.perf_counter() - t0))
            prof_path.write_text(json.dumps(prof_json, indent=2), encoding="utf-8")
            print("—" * 60)
            print("Profiling summary (seconds):")
            for key in (
                "recording_sec",
                "model_load_sec",
                "transcribe_sec",
                "clipboard_sec",
                "total_sec",
            ):
                if key in prof_json:
                    print(f"  {key}: {prof_json[key]:.3f}")
            print(f"Saved profiling JSON: {prof_path}")
        except Exception as e:
            print(f"Warning: failed to write profiling JSON: {e}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record speech, transcribe with Whisper, emit outputs, and copy .txt to clipboard."
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "-l",
        "--lang",
        help="Whisper language (e.g., 'de' or 'en'); auto-detect if omitted",
        default=None,
    )
    parser.add_argument(
        "-r", "--rate", type=int, default=44100, help="Sample rate (default: 44100)"
    )
    parser.add_argument(
        "-c", "--channels", type=int, default=1, help="Channels (1=mono, 2=stereo; default: 1)"
    )
    parser.add_argument(
        "-m",
        "--model",
        default="turbo",
        help="Whisper model (e.g., turbo, base, small, medium, large-v2)",
    )
    parser.add_argument(
        "-f",
        "--recording-format",
        choices=["flac", "wav", "mp3"],
        default="flac",
        help="Audio container for the recording (default: flac)",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default=None,
        help="Base output directory for timestamped sessions (default: current directory)",
    )
    parser.add_argument(
        "-t",
        "--translate",
        action="store_true",
        help="After transcription, translate all outputs to English (post-processing)",
    )
    parser.add_argument(
        "--translate-to",
        action="append",
        default=None,
        help="After transcription, translate all outputs to the given language (can be repeated)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print details about the Whisper invocation",
    )
    parser.add_argument(
        "-L",
        "--list-models",
        action="store_true",
        help="List available Whisper model names and exit",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Collect and print timing information; also writes profile.json to the session folder",
    )
    parser.add_argument(
        "--debounce-ms",
        type=int,
        default=0,
        help="Debounce window for SPACE (ms). If >0, ignores rapid successive space presses",
    )
    parser.add_argument(
        "--silence-sec",
        type=float,
        default=2.0,
        help="Auto-split when continuous silence >= this many seconds (0 disables)",
    )
    parser.add_argument(
        "--min-chunk-sec",
        type=float,
        default=5.0,
        help="Minimum duration a chunk must reach before auto-split can trigger",
    )
    parser.add_argument(
        "--chunk-segmentation",
        action="store_true",
        help="Disable Whisper's native segmentation: emit exactly one segment per recorded chunk",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        action="store_true",
        help="Spoken prompt mode: speak your prompt, then press SPACE to use it as prompt and continue with payload; if you press ENTER instead, no prompt is used and the spoken audio is transcribed as normal payload before ending",
    )
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="Keep per-chunk audio and outputs (default: delete after final merge)",
    )
    parser.add_argument(
        "-e",
        "--edit",
        action="store_true",
        help="Open the transcript (.txt) in the system's default editor instead of printing to stdout",
    )
    args = parser.parse_args(argv)

    try:
        if args.list_models:
            try:
                import whisper

                models = sorted(whisper.available_models())
                print("Available models:")
                for m in models:
                    print(f"  - {m}")
                return 0
            except Exception as e:
                print(f"Error listing models: {e}", file=sys.stderr)
                return 1
        logging.basicConfig(
            level=(logging.INFO if args.verbose else logging.WARNING),
            format="%(levelname)s: %(message)s",
        )
        # Default outdir to 'transcripts' if not provided
        opts = SessionOptions(
            outdir=Path(args.outdir) if args.outdir else Path("transcripts"),
            rate=args.rate,
            channels=args.channels,
            recording_format=args.recording_format,
            model=args.model,
            lang=args.lang,
            translate=args.translate,
            translate_to=(args.translate_to or []),
            native_segmentation=(not getattr(args, "chunk_segmentation", False)),
            verbose=args.verbose,
            edit=args.edit,
            debounce_ms=getattr(args, "debounce_ms", 0),
            silence_sec=getattr(args, "silence_sec", 1.0),
            min_chunk_sec=getattr(args, "min_chunk_sec", 5.0),
            profile=args.profile,
            keep_chunks=getattr(args, "keep_chunks", False),
            prompt=getattr(args, "prompt", False),
        )
        return run_session(opts)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
