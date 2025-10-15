from __future__ import annotations

from pathlib import Path

from .types import TranscriptionResult


def write_final_outputs(
    merged_result: TranscriptionResult, session_dir: Path, base_audio_path: Path
) -> Path:
    try:
        from whisper.utils import get_writer

        for fmt in ("txt", "srt", "vtt", "tsv", "json"):
            writer = get_writer(fmt, str(session_dir))
            writer(merged_result, str(base_audio_path))
        return session_dir / "recording.txt"
    except Exception as e:
        print(f"Error writing merged outputs: {e}")
        txt_path = session_dir / "recording.txt"
        try:
            txt_path.write_text(merged_result.get("text", ""), encoding="utf-8")
        except Exception:
            pass
        return txt_path


def concat_audio(
    chunk_paths: list[Path],
    out_path: Path,
    samplerate: int,
    channels: int,
) -> None:
    try:
        import soundfile as sf

        fmt = "FLAC" if out_path.suffix.lower() == ".flac" else "WAV"
        with sf.SoundFile(
            str(out_path), mode="w", samplerate=samplerate, channels=channels, format=fmt
        ) as outf:
            for p in chunk_paths:
                with sf.SoundFile(str(p), mode="r") as inf:
                    while True:
                        data = inf.read(frames=16384, dtype="float32")
                        if data.size == 0:
                            break
                        outf.write(data)
    except Exception as e:
        print(f"Warning: failed to merge chunk audio: {e}")
