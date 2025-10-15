from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


def check_dependency(cmd: str, install_hint: str) -> None:
    if shutil.which(cmd) is None:
        raise RuntimeError(f"Dependency '{cmd}' not found. Hint: {install_hint}")


def convert_wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    check_dependency(
        "ffmpeg",
        "macOS: brew install ffmpeg; Linux: apt/yum; Windows: install ffmpeg and add to PATH",
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(wav_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(mp3_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def copy_to_clipboard(text: str) -> None:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return
        if system == "Windows":
            subprocess.run(["clip"], input=text, text=True, check=True)
            return
        if shutil.which("xclip"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
            return
        if shutil.which("xsel"):
            subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True)
            return
        try:
            import pyperclip

            pyperclip.copy(text)
            return
        except Exception:
            pass
    except Exception as e:
        print(f"Copy to clipboard failed: {e}", file=sys.stderr)
        return
    print("No clipboard tool found (pbcopy/clip/xclip/xsel). Optional: pip install pyperclip.")


def open_in_shell_editor(file_path: Path) -> tuple[bool, str]:
    env_editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    candidates: list[list[str]] = []
    if env_editor:
        import shlex as _shlex

        try:
            candidates.append(_shlex.split(env_editor))
        except Exception:
            candidates.append([env_editor])
    candidates += [["vim"], ["nvim"], ["nano"], ["micro"], ["notepad"]]
    for argv in candidates:
        exe = argv[0]
        if shutil.which(exe) is None:
            continue
        try:
            subprocess.run(argv + [str(file_path)], check=True)
            return True, " ".join(argv)
        except Exception:
            continue
    return False, ""


def make_session_dir(base_dir: Path | None = None) -> Path:
    ts = datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S%z")
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    base.mkdir(parents=True, exist_ok=True)
    session = base / ts
    session.mkdir(parents=True, exist_ok=False)
    return session


def resample_linear(x: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return x.astype(np.float32, copy=False)
    x = x.astype(np.float32, copy=False)
    n_src = x.shape[0]
    n_dst = int(round(n_src * (dst_sr / float(src_sr))))
    if n_src == 0 or n_dst == 0:
        return np.zeros(n_dst, dtype=np.float32)
    src_t = np.linspace(0.0, 1.0, num=n_src, endpoint=False)
    dst_t = np.linspace(0.0, 1.0, num=n_dst, endpoint=False)
    return np.interp(dst_t, src_t, x).astype(np.float32)
