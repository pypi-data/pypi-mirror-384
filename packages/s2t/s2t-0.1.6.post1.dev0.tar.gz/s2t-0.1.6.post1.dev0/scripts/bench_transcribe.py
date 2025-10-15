#!/usr/bin/env python3
"""
Simple benchmarking for Whisper transcription to compare cold vs. warm runs.

Examples:
  python scripts/bench_transcribe.py --file transcripts/sample.flac --runs 3 --model large-v3
  python scripts/bench_transcribe.py --file transcripts/sample.flac --runs 3 --model large-v3 --reuse-model
  python scripts/bench_transcribe.py --file transcripts/sample.flac --runs 3 --translate
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np


def _resample_linear(x: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return x.astype(np.float32, copy=False)
    x = x.astype(np.float32, copy=False)
    n_src = x.shape[0]
    n_dst = int(round(n_src * (dst_sr / float(src_sr))))
    if n_src == 0 or n_dst == 0:
        return np.zeros(n_dst, dtype=np.float32)
    import numpy as _np

    src_t = _np.linspace(0.0, 1.0, num=n_src, endpoint=False)
    dst_t = _np.linspace(0.0, 1.0, num=n_dst, endpoint=False)
    return _np.interp(dst_t, src_t, x).astype(np.float32)


def _load_audio_for_model(path: Path) -> np.ndarray | None:
    # Avoid ffmpeg for non-mp3
    if path.suffix.lower() == ".mp3":
        return None
    try:
        import soundfile as sf  # type: ignore

        data, sr = sf.read(str(path), always_2d=False)
        if isinstance(data, np.ndarray) and data.ndim == 2:
            data = data.mean(axis=1)
        return _resample_linear(np.asarray(data, dtype=np.float32), sr, 16000)
    except Exception:
        return None


def bench(
    file: Path, runs: int, model_name: str, language: str | None, translate: bool, reuse_model: bool
) -> dict:
    import whisper  # type: ignore

    audio_arr = _load_audio_for_model(file)
    task = "translate" if translate else "transcribe"
    times = []
    model = None
    if reuse_model:
        t0 = time.perf_counter()
        model = whisper.load_model(model_name)
        t1 = time.perf_counter()
        times.append({"model_load_sec": t1 - t0, "transcribe_sec": 0.0})
    for _i in range(runs):
        t_load0 = time.perf_counter()
        if not reuse_model:
            model = whisper.load_model(model_name)
        t_load1 = time.perf_counter()
        t_tx0 = time.perf_counter()
        _ = model.transcribe(
            audio_arr if audio_arr is not None else str(file),
            task=task,
            language=language,
            fp16=False,
        )
        t_tx1 = time.perf_counter()
        times.append(
            {
                "model_load_sec": (t_load1 - t_load0) if not reuse_model else 0.0,
                "transcribe_sec": t_tx1 - t_tx0,
            }
        )
    return {
        "file": str(file),
        "runs": runs,
        "model": model_name,
        "language": language,
        "task": task,
        "results": times,
        "avg_model_load_sec": sum(t["model_load_sec"] for t in times) / len(times),
        "avg_transcribe_sec": sum(t["transcribe_sec"] for t in times) / len(times),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Benchmark Whisper transcription performance")
    p.add_argument("--file", required=True, help="Audio file (flac/wav/mp3)")
    p.add_argument("--runs", type=int, default=3, help="Number of runs")
    p.add_argument("--model", default="base", help="Model name (e.g., base, small, large-v3)")
    p.add_argument("--lang", default=None, help="Language hint (e.g., de, en)")
    p.add_argument("--translate", action="store_true", help="Use translate task (to English)")
    p.add_argument(
        "--reuse-model", action="store_true", help="Load model once and reuse across runs"
    )
    p.add_argument("--json-out", default=None, help="Write JSON to file path")
    args = p.parse_args(argv)

    file = Path(args.file)
    res = bench(file, args.runs, args.model, args.lang, args.translate, args.reuse_model)
    print("Benchmark summary:")
    print(f"  file: {res['file']}")
    print(f"  model: {res['model']}  task: {res['task']}  lang: {res['language']}")
    print(f"  runs: {res['runs']}")
    print(f"  avg model load (s): {res['avg_model_load_sec']:.3f}")
    print(f"  avg transcribe (s): {res['avg_transcribe_sec']:.3f}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"  wrote JSON: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
