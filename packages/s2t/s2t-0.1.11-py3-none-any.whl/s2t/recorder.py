from __future__ import annotations

import os
import queue
import select
import sys
import threading
import time
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import numpy as np

from .utils import debug_log


class Recorder:
    def __init__(
        self,
        session_dir: Path,
        samplerate: int,
        channels: int,
        ext: str,
        debounce_ms: int = 0,
        verbose: bool = False,
        pause_after_first_chunk: bool = False,
        resume_event: threading.Event | None = None,
        silence_sec: float = 1.0,
        min_chunk_sec: float = 5.0,
    ) -> None:
        self.session_dir = session_dir
        self.samplerate = samplerate
        self.channels = channels
        self.ext = ext
        self.debounce_ms = max(0, int(debounce_ms))
        self.verbose = verbose
        self.pause_after_first_chunk = pause_after_first_chunk
        self.resume_event = resume_event
        self._paused = False
        # Auto-split config
        self.silence_sec = max(0.0, float(silence_sec))
        self.min_chunk_sec = max(0.0, float(min_chunk_sec))

    def run(
        self,
        tx_queue: queue.Queue[tuple[int, Path, int, float, str]],
    ) -> tuple[list[Path], list[int], list[float]]:
        import platform
        import termios
        import tty

        try:
            import sounddevice as sd
            import soundfile as sf
        except Exception as e:
            raise RuntimeError("sounddevice/soundfile required for recording.") from e

        evt_q: queue.Queue[str] = queue.Queue()
        # Control queue is separate from audio frames to avoid control backpressure.
        ctrl_q: queue.Queue[str] = queue.Queue()
        stop_evt = threading.Event()

        def key_reader() -> None:
            try:
                if platform.system() == "Windows":
                    import msvcrt

                    @runtime_checkable
                    class _MSVCRT(Protocol):
                        def kbhit(self) -> int: ...
                        def getwch(self) -> str: ...

                    ms = cast(_MSVCRT, msvcrt)

                    last_space = 0.0
                    debug_log(self.verbose, "recorder", "Key input: using msvcrt (Windows)")
                    while not stop_evt.is_set():
                        if ms.kbhit():
                            ch = ms.getwch()
                            if ch in ("\r", "\n"):
                                debug_log(self.verbose, "recorder", "Key input: ENTER")
                                evt_q.put("ENTER")
                                break
                            if ch == " ":
                                now = time.perf_counter()
                                if self.debounce_ms and (now - last_space) < (
                                    self.debounce_ms / 1000.0
                                ):
                                    continue
                                last_space = now
                                debug_log(self.verbose, "recorder", "Key input: SPACE")
                                evt_q.put("SPACE")
                        time.sleep(0.01)
                else:
                    # Prefer sys.stdin when it's a TTY (original, proven path). If not a TTY, try /dev/tty, else fallback to stdin line reads.
                    try:
                        if sys.stdin.isatty():
                            fd = sys.stdin.fileno()
                            debug_log(
                                self.verbose, "recorder", "Key input: using sys.stdin (TTY fd read)"
                            )
                            old = termios.tcgetattr(fd)
                            tty.setcbreak(fd)
                            last_space = 0.0
                            try:
                                while not stop_evt.is_set():
                                    r, _, _ = select.select([fd], [], [], 0.05)
                                    if r:
                                        try:
                                            ch_b = os.read(fd, 1)
                                        except BlockingIOError:
                                            continue
                                        if not ch_b:
                                            continue
                                        ch = ch_b.decode(errors="ignore")
                                        if ch in ("\n", "\r"):
                                            debug_log(self.verbose, "recorder", "Key input: ENTER")
                                            evt_q.put("ENTER")
                                            break
                                        if ch == " ":
                                            now = time.perf_counter()
                                            if self.debounce_ms and (now - last_space) < (
                                                self.debounce_ms / 1000.0
                                            ):
                                                continue
                                            last_space = now
                                            debug_log(self.verbose, "recorder", "Key input: SPACE")
                                            evt_q.put("SPACE")
                            finally:
                                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                        else:
                            # Try /dev/tty when stdin is not a TTY
                            using_devtty = False
                            fd = None
                            try:
                                fd = os.open("/dev/tty", os.O_RDONLY)
                                using_devtty = True
                                debug_log(
                                    self.verbose,
                                    "recorder",
                                    "Key input: using /dev/tty (stdin not TTY)",
                                )
                                old = termios.tcgetattr(fd)
                                tty.setcbreak(fd)
                                last_space = 0.0
                                try:
                                    while not stop_evt.is_set():
                                        r, _, _ = select.select([fd], [], [], 0.05)
                                        if r:
                                            ch_b = os.read(fd, 1)
                                            if not ch_b:
                                                continue
                                            ch = ch_b.decode(errors="ignore")
                                            if ch in ("\n", "\r"):
                                                debug_log(
                                                    self.verbose, "recorder", "Key input: ENTER"
                                                )
                                                evt_q.put("ENTER")
                                                break
                                            if ch == " ":
                                                now = time.perf_counter()
                                                if self.debounce_ms and (now - last_space) < (
                                                    self.debounce_ms / 1000.0
                                                ):
                                                    continue
                                                last_space = now
                                                debug_log(
                                                    self.verbose, "recorder", "Key input: SPACE"
                                                )
                                                evt_q.put("SPACE")
                                finally:
                                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
                            except Exception:
                                if using_devtty and fd is not None:
                                    try:
                                        os.close(fd)
                                    except Exception:
                                        pass
                                print(
                                    "Warning: no TTY for key input; falling back to stdin line mode.",
                                    file=sys.stderr,
                                )
                                # Last resort: line-buffered stdin; Enter will still end.
                                while not stop_evt.is_set():
                                    line = sys.stdin.readline()
                                    if not line:
                                        time.sleep(0.05)
                                        continue
                                    # If user hits Enter on empty line, treat as ENTER
                                    if line == "\n" or line == "\r\n":
                                        debug_log(
                                            self.verbose, "recorder", "Key input: ENTER (line mode)"
                                        )
                                        evt_q.put("ENTER")
                                        break
                                    # If first non-empty char is space, treat as SPACE
                                    if line and line[0] == " ":
                                        debug_log(
                                            self.verbose, "recorder", "Key input: SPACE (line mode)"
                                        )
                                        evt_q.put("SPACE")
                    except Exception as e:
                        print(f"Warning: key reader failed: {e}", file=sys.stderr)

            except Exception as e:
                # Log unexpected key reader errors to aid debugging, but keep recording running.
                print(f"Warning: key reader stopped unexpectedly: {e}", file=sys.stderr)

        # Unbounded audio queue to avoid drops on slower machines; control signals are separate.
        audio_q: queue.Queue[tuple[str, Any]] = queue.Queue()
        chunk_index = 1
        chunk_paths: list[Path] = []
        chunk_frames: list[int] = []
        chunk_offsets: list[float] = []
        offset_seconds_total = 0.0

        def writer_fn() -> None:
            nonlocal chunk_index, offset_seconds_total
            frames_written = 0
            cur_path = self.session_dir / f"chunk_{chunk_index:04d}{self.ext}"
            fh = sf.SoundFile(
                str(cur_path), mode="w", samplerate=self.samplerate, channels=self.channels
            )
            # State for auto-split based on silence
            silent_frames_run = 0
            seen_non_silent = False
            last_split_time = 0.0
            # Internal thresholds
            threshold_rms = 0.015  # conservative RMS threshold for float32 [-1,1]
            split_cooldown_sec = 0.2

            def _do_split(cause: str) -> None:
                nonlocal fh, frames_written, cur_path, chunk_index, offset_seconds_total
                fh.flush()
                fh.close()
                if frames_written > 0:
                    dur = frames_written / float(self.samplerate)
                    chunk_paths.append(cur_path)
                    chunk_frames.append(frames_written)
                    chunk_offsets.append(offset_seconds_total)
                    offset_seconds_total += dur
                    debug_log(
                        self.verbose,
                        "recorder",
                        f"Saved chunk {chunk_index}: {cur_path.name} ({dur:.2f}s)",
                    )
                    # Include split cause so downstream can format output accordingly
                    # cause: "space" (manual split) or "pause" (auto-split)
                    tx_queue.put((chunk_index, cur_path, frames_written, chunk_offsets[-1], cause))
                    debug_log(
                        self.verbose,
                        "recorder",
                        f"Enqueued chunk {chunk_index} for transcription (cause={cause})",
                    )
                else:
                    try:
                        cur_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                frames_written = 0
                chunk_index += 1
                if (
                    self.pause_after_first_chunk
                    and chunk_index == 2
                    and self.resume_event is not None
                ):
                    self._paused = True
                    debug_log(
                        self.verbose,
                        "recorder",
                        "Paused after first chunk; waiting for resume (prompt mode)",
                    )
                    self.resume_event.wait()
                    self._paused = False
                    debug_log(self.verbose, "recorder", "Resumed after prompt")
                cur_path = self.session_dir / f"chunk_{chunk_index:04d}{self.ext}"
                fh = sf.SoundFile(
                    str(cur_path),
                    mode="w",
                    samplerate=self.samplerate,
                    channels=self.channels,
                )
                # Reset silence tracking after a split
                return

            while True:
                # First, handle any pending control commands so SPACE/ENTER are never blocked by frames backlog.
                try:
                    while True:
                        cmd = ctrl_q.get_nowait()
                        if cmd == "split_manual":
                            _do_split("space")
                            # Reset silence tracking on manual split
                            silent_frames_run = 0
                            seen_non_silent = False
                        elif cmd == "split_auto":
                            _do_split("pause")
                            # Reset silence tracking on manual split
                            silent_frames_run = 0
                            seen_non_silent = False
                        elif cmd == "finish":
                            fh.flush()
                            fh.close()
                            if frames_written > 0:
                                dur = frames_written / float(self.samplerate)
                                chunk_paths.append(cur_path)
                                chunk_frames.append(frames_written)
                                chunk_offsets.append(offset_seconds_total)
                                offset_seconds_total += dur
                                debug_log(
                                    self.verbose,
                                    "recorder",
                                    f"Saved chunk {chunk_index}: {cur_path.name} ({dur:.2f}s)",
                                )
                                # Final chunk – mark cause as "finish" so downstream can avoid extra blank spacing
                                tx_queue.put(
                                    (
                                        chunk_index,
                                        cur_path,
                                        frames_written,
                                        chunk_offsets[-1],
                                        "finish",
                                    )
                                )
                                debug_log(
                                    self.verbose,
                                    "recorder",
                                    f"Enqueued final chunk {chunk_index} for transcription",
                                )
                            else:
                                try:
                                    cur_path.unlink(missing_ok=True)
                                except Exception:
                                    pass
                            tx_queue.put((-1, Path(), 0, 0.0, ""))
                            debug_log(self.verbose, "recorder", "Signaled transcription finish")
                            return
                except queue.Empty:
                    pass

                # Then, write frames if available; short timeout to re-check control queue regularly.
                try:
                    kind, payload = audio_q.get(timeout=0.05)
                except queue.Empty:
                    continue
                if kind == "frames":
                    data = payload
                    fh.write(data)
                    frames_written += len(data)
                    # Auto-split based on silence if enabled
                    if self.silence_sec > 0.0:
                        try:
                            arr = np.asarray(data, dtype=np.float32)
                            if arr.ndim == 2 and arr.shape[1] > 1:
                                # average channels
                                arr_mono = arr.mean(axis=1)
                            else:
                                arr_mono = arr.reshape(-1)
                            # compute RMS
                            rms = (
                                float(np.sqrt(np.mean(np.square(arr_mono))))
                                if arr_mono.size
                                else 0.0
                            )
                        except Exception:
                            rms = 0.0

                        if rms < threshold_rms:
                            silent_frames_run += len(arr_mono)
                        else:
                            silent_frames_run = 0
                            seen_non_silent = True

                        # Conditions to auto-split
                        enough_silence = silent_frames_run >= int(
                            self.samplerate * self.silence_sec
                        )
                        enough_length = frames_written >= int(self.samplerate * self.min_chunk_sec)
                        cooldown_ok = (time.perf_counter() - last_split_time) >= split_cooldown_sec
                        if enough_silence and enough_length and seen_non_silent and cooldown_ok:
                            debug_log(
                                self.verbose,
                                "recorder",
                                f"Auto-split (≥{self.silence_sec:.2f}s silence)",
                            )
                            last_split_time = time.perf_counter()
                            # Queue an auto split for the next control phase
                            ctrl_q.put("split_auto")
                            # Reset silence tracking now to avoid cascaded triggers
                            silent_frames_run = 0
                            seen_non_silent = False
            tx_queue.put((-1, Path(), 0, 0.0, ""))

        def cb(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            if status:
                print(status, file=sys.stderr)
            if not self._paused:
                audio_q.put(("frames", indata.copy()))

        key_t = threading.Thread(target=key_reader, daemon=True)
        writer_t = threading.Thread(target=writer_fn, daemon=True)
        key_t.start()
        writer_t.start()

        msg = "Recording… Press SPACE to split, Enter to finish."
        if self.silence_sec > 0.0:
            msg += (
                f" Auto-split on ≥{self.silence_sec:.2f}s silence (min {self.min_chunk_sec:.2f}s)."
            )
        print(msg)
        print("—" * 60)
        print("")

        debug_log(
            self.verbose,
            "recorder",
            f"Recording started (rate={self.samplerate}, channels={self.channels}, ext={self.ext})",
        )

        import sounddevice as sd

        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=cb):
            while True:
                try:
                    evt = evt_q.get(timeout=0.05)
                except queue.Empty:
                    continue
                if evt == "SPACE":
                    ctrl_q.put("split_manual")
                elif evt == "ENTER":
                    ctrl_q.put("finish")
                    break
        writer_t.join()
        debug_log(self.verbose, "recorder", "Recording finished")
        return chunk_paths, chunk_frames, chunk_offsets
