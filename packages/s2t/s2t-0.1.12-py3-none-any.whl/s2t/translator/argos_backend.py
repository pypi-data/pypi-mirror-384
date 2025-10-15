from __future__ import annotations

import os
import platform
import threading
import time
from collections.abc import Iterable
from pathlib import Path

from ..types import SegmentDict, TranscriptionResult
from ..utils import debug_log

# Global install coordination to avoid duplicate downloads in parallel
_install_lock = threading.Lock()
_inflight: dict[tuple[str, str], threading.Event] = {}


class ArgosTranslator:
    """Thin wrapper around argostranslate for install + translate.

    This module performs automatic package installation (network required once)
    and then translates text fully offline.
    """

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _debug(self, msg: str) -> None:
        debug_log(self.verbose, "argos", msg)

    @staticmethod
    def _guess_packages_dir() -> str:
        try:
            system = platform.system().lower()
            home = Path.home()
            candidates: list[Path] = []
            if system == "darwin":
                candidates.append(
                    home / "Library" / "Application Support" / "argos-translate" / "packages"
                )
                candidates.append(home / ".local" / "share" / "argos-translate" / "packages")
            elif system == "windows":
                appdata = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
                localapp = os.environ.get("LOCALAPPDATA") or str(home / "AppData" / "Local")
                candidates.append(Path(appdata) / "argos-translate" / "packages")
                candidates.append(Path(localapp) / "argos-translate" / "packages")
            else:
                candidates.append(home / ".local" / "share" / "argos-translate" / "packages")
            for p in candidates:
                if p.exists():
                    return str(p)
            return str(candidates[0]) if candidates else "(unknown)"
        except Exception as e:
            return f"(unknown: {type(e).__name__}: {e})"

    def ensure_package(self, src_lang: str, dst_lang: str) -> bool:
        """Ensure Argos package for src->dst is installed. Returns True if ready.

        Attempts to install automatically if missing.
        """
        try:
            # Avoid importing unless needed so users without argostranslate can still run ASR-only.
            import argostranslate.package as argos_pkg
        except Exception:  # pragma: no cover - external dep
            # Keep core tool functional if argostranslate is not present
            self._debug(
                "Argos: argostranslate not installed; cannot auto-install translation packages."
            )
            return False

        src = src_lang.lower()
        dst = dst_lang.lower()
        if src == dst:
            return True

        # Fast path: already installed (direct or pivot path)
        if self.has_package(src, dst):
            return True

        # Coordinate installs to avoid duplicate downloads across threads
        pair = (src, dst)
        with _install_lock:
            ev = _inflight.get(pair)
            if ev is None:
                ev = threading.Event()
                _inflight[pair] = ev
                starter = True
            else:
                starter = False

        if not starter:
            # Another thread is installing this pair; wait for completion
            if self.verbose:
                self._debug(f"Argos: waiting for ongoing install {src}->{dst} to finish…")
            ev.wait(timeout=600.0)
            return self.has_package(src, dst)

        try:
            # We are the installer for this pair
            packages_dir = self._guess_packages_dir()

            # Update package index once per install attempt
            try:
                if self.verbose:
                    self._debug("Argos: updating package index…")
                argos_pkg.update_package_index()
            except Exception as e_upd:
                if self.verbose:
                    self._debug(
                        f"Argos: update_package_index failed: {type(e_upd).__name__}: {e_upd}"
                    )

            available = []
            try:
                available = argos_pkg.get_available_packages()
            except Exception as e_av:
                if self.verbose:
                    self._debug(
                        f"Argos: get_available_packages failed: {type(e_av).__name__}: {e_av}"
                    )

            # Attempt direct first
            cand = next(
                (
                    p
                    for p in available
                    if getattr(p, 'from_code', None) == src and getattr(p, 'to_code', None) == dst
                ),
                None,
            )
            if cand is not None:
                if self.verbose:
                    self._debug(
                        f"Argos: downloading package {src}->{dst} -> install into {packages_dir}"
                    )
                try:
                    path = cand.download()
                    if self.verbose:
                        self._debug(f"Argos: downloaded file for {src}->{dst}: {path}")
                    argos_pkg.install_from_path(path)
                    if self.verbose:
                        self._debug(f"Argos: installed package {src}->{dst}")
                except Exception as e_dir:
                    if self.verbose:
                        self._debug(
                            f"Argos: install {src}->{dst} failed: {type(e_dir).__name__}: {e_dir}"
                        )

            # If still not available, try pivot via English
            if not self.has_package(src, dst):
                pivot = "en"
                if self.verbose:
                    self._debug(
                        f"Argos: no direct package {src}->{dst} in index; trying pivot via {pivot} [{src}->{pivot}, {pivot}->{dst}]"
                    )
                cand1 = next(
                    (
                        p
                        for p in available
                        if getattr(p, 'from_code', None) == src
                        and getattr(p, 'to_code', None) == pivot
                    ),
                    None,
                )
                cand2 = next(
                    (
                        p
                        for p in available
                        if getattr(p, 'from_code', None) == pivot
                        and getattr(p, 'to_code', None) == dst
                    ),
                    None,
                )
                if cand1 is None and cand2 is None and self.verbose:
                    self._debug(
                        f"Argos: no direct or pivot packages available for {src}->{dst} in index"
                    )
                if cand1 is not None:
                    # coordinate concrete edge (src->pivot)
                    edge = (src, pivot)
                    with _install_lock:
                        ev_edge = _inflight.get(edge)
                        if ev_edge is None:
                            ev_edge = threading.Event()
                            _inflight[edge] = ev_edge
                            edge_starter = True
                        else:
                            edge_starter = False
                    if not edge_starter:
                        if self.verbose:
                            self._debug(
                                f"Argos: waiting for ongoing install {src}->{pivot} to finish…"
                            )
                        ev_edge.wait(timeout=600.0)
                    else:
                        try:
                            if self.verbose:
                                self._debug(
                                    f"Argos: downloading package {src}->{pivot} -> install into {packages_dir}"
                                )
                            path1 = cand1.download()
                            if self.verbose:
                                self._debug(f"Argos: downloaded file for {src}->{pivot}: {path1}")
                            argos_pkg.install_from_path(path1)
                            if self.verbose:
                                self._debug(f"Argos: installed package {src}->{pivot}")
                        except Exception as e1:
                            if self.verbose:
                                self._debug(
                                    f"Argos: install {src}->{pivot} failed: {type(e1).__name__}: {e1}"
                                )
                        finally:
                            with _install_lock:
                                ev_done = _inflight.get(edge)
                                if ev_done is not None:
                                    ev_done.set()
                                    _inflight.pop(edge, None)
                if cand2 is not None:
                    # coordinate concrete edge (pivot->dst)
                    edge = (pivot, dst)
                    with _install_lock:
                        ev_edge = _inflight.get(edge)
                        if ev_edge is None:
                            ev_edge = threading.Event()
                            _inflight[edge] = ev_edge
                            edge_starter = True
                        else:
                            edge_starter = False
                    if not edge_starter:
                        if self.verbose:
                            self._debug(
                                f"Argos: waiting for ongoing install {pivot}->{dst} to finish…"
                            )
                        ev_edge.wait(timeout=600.0)
                    else:
                        try:
                            if self.verbose:
                                self._debug(
                                    f"Argos: downloading package {pivot}->{dst} -> install into {packages_dir}"
                                )
                            path2 = cand2.download()
                            if self.verbose:
                                self._debug(f"Argos: downloaded file for {pivot}->{dst}: {path2}")
                            argos_pkg.install_from_path(path2)
                            if self.verbose:
                                self._debug(f"Argos: installed package {pivot}->{dst}")
                        except Exception as e2:
                            if self.verbose:
                                self._debug(
                                    f"Argos: install {pivot}->{dst} failed: {type(e2).__name__}: {e2}"
                                )
                        finally:
                            with _install_lock:
                                ev_done = _inflight.get(edge)
                                if ev_done is not None:
                                    ev_done.set()
                                    _inflight.pop(edge, None)

            # Final check (direct or pivot should now be available)
            return self.has_package(src, dst)
        finally:
            with _install_lock:
                ev = _inflight.get(pair)
                if ev is not None:
                    ev.set()
                    _inflight.pop(pair, None)

    def translate_texts(self, texts: Iterable[str], src_lang: str, dst_lang: str) -> list[str]:
        import argostranslate.translate as argos_tr

        src = src_lang.lower()
        dst = dst_lang.lower()
        installed = argos_tr.get_installed_languages()
        src_lang_obj = next((lang for lang in installed if getattr(lang, "code", "") == src), None)
        dst_lang_obj = next((lang for lang in installed if getattr(lang, "code", "") == dst), None)
        if not (src_lang_obj and dst_lang_obj):
            raise RuntimeError(
                f"Argos package not installed for {src}->{dst}. Installation should have been attempted earlier."
            )

        # Try direct translation first
        t_direct = None
        try:
            t_direct = src_lang_obj.get_translation(dst_lang_obj)
        except Exception:
            t_direct = None

        if t_direct is not None:
            out: list[str] = []
            for s in texts:
                out.append(t_direct.translate(s or ""))
            return out

        # Fallback: pivot via English if both edges exist
        pivot_code = "en"
        pivot_lang_obj = next(
            (lang for lang in installed if getattr(lang, "code", "") == pivot_code), None
        )
        if pivot_lang_obj is None:
            raise RuntimeError(
                f"Argos package not installed for {src}->{dst} and no pivot via {pivot_code} available."
            )
        try:
            t_src_pivot = src_lang_obj.get_translation(pivot_lang_obj)
            t_pivot_dst = pivot_lang_obj.get_translation(dst_lang_obj)
        except Exception as e:
            raise RuntimeError(
                f"Argos direct translator {src}->{dst} missing and cannot pivot via {pivot_code}: {e}"
            ) from e

        if self.verbose:
            packages_dir = self._guess_packages_dir()
            self._debug(
                f"Argos: using pivot via {pivot_code} (packages dir: {packages_dir}) for {src}->{dst}"
            )
        # First hop src->pivot, then pivot->dst
        mid: list[str] = []
        for s in texts:
            mid.append(t_src_pivot.translate(s or ""))
        out2: list[str] = []
        for m in mid:
            out2.append(t_pivot_dst.translate(m or ""))
        return out2

    def has_package(self, src_lang: str, dst_lang: str) -> bool:
        """Return True if a translation from src->dst is currently installed."""
        try:
            import argostranslate.translate as argos_tr

            src = src_lang.lower()
            dst = dst_lang.lower()
            installed = argos_tr.get_installed_languages()
            src_lang_obj = next(
                (lang for lang in installed if getattr(lang, "code", "") == src), None
            )
            dst_lang_obj = next(
                (lang for lang in installed if getattr(lang, "code", "") == dst), None
            )
            if not (src_lang_obj and dst_lang_obj):
                return False
            # True if direct exists or if a pivot path via 'en' exists
            try:
                _ = src_lang_obj.get_translation(dst_lang_obj)
                return True
            except Exception:
                # Check pivot path
                pivot_code = "en"
                pivot_lang_obj = next(
                    (lang for lang in installed if getattr(lang, "code", "") == pivot_code), None
                )
                if not pivot_lang_obj:
                    return False
                try:
                    _ = src_lang_obj.get_translation(pivot_lang_obj)
                    _ = pivot_lang_obj.get_translation(dst_lang_obj)
                    return True
                except Exception:
                    return False
        except Exception:
            return False


def ensure_packages_background(
    translator: ArgosTranslator,
    src_lang_hint: str | None,
    target_langs: list[str],
    detected_lang_event: threading.Event | None = None,
    detected_lang_holder: dict[str, str | None] | None = None,
) -> None:
    """Start background thread to ensure Argos packages exist.

    - If src_lang_hint is provided, install immediately for that source.
    - Otherwise, wait for detected_lang_event to fire and then install for the detected source.
    """

    def _runner() -> None:
        # First, try to update index early to avoid later blocking.
        try:
            import argostranslate.package as argos_pkg

            argos_pkg.update_package_index()
        except Exception:
            # offline is OK; will skip install later
            pass

        src = (src_lang_hint or "").strip().lower()
        if not src:
            if detected_lang_event is not None and detected_lang_holder is not None:
                detected_lang_event.wait(timeout=300.0)
                src = (detected_lang_holder.get("code") or "").strip().lower()
        if not src:
            # Could not determine source language; give up silently
            return
        for tgt in dict.fromkeys([t.lower() for t in target_langs if t]):
            if tgt == src:
                continue
            try:
                translator.ensure_package(src, tgt)
            except Exception:
                # swallow background errors
                pass

    t = threading.Thread(target=_runner, daemon=True)
    t.start()


def translate_result_segments(
    translator: ArgosTranslator,
    result: TranscriptionResult,
    src_lang: str,
    dst_lang: str,
) -> TranscriptionResult:
    """Translate a merged TranscriptionResult segment-wise, preserving timing.

    Returns a new TranscriptionResult with translated text and segments.
    """
    segs = result.get("segments", []) or []
    if segs:
        orig_texts: list[str] = [str(s.get("text") or "") for s in segs]
        translated = translator.translate_texts(orig_texts, src_lang, dst_lang)
        new_segs: list[SegmentDict] = []
        for s, tt in zip(segs, translated, strict=False):
            seg_out: SegmentDict = {}
            if "start" in s:
                seg_out["start"] = float(s["start"])  # s['start'] is float in SegmentDict
            if "end" in s:
                seg_out["end"] = float(s["end"])  # s['end'] is float in SegmentDict
            seg_out["text"] = str(tt)
            new_segs.append(seg_out)
        joined_text = "".join([str(s.get("text", "")) for s in new_segs])
        return {"text": joined_text, "segments": new_segs}
    # Fallback: no segments, translate whole text
    whole = result.get("text", "")
    tt = translator.translate_texts([whole], src_lang, dst_lang)[0]
    return {"text": tt, "segments": []}


def wait_for_packages(
    translator: ArgosTranslator,
    src_lang: str,
    targets: list[str],
    max_wait_s: float = 120.0,
    verbose: bool = False,
) -> set[str]:
    """Wait until required packages are installed or timeout expires.

    Returns the set of target codes that are ready. This function polls the
    translator for installed status, while a background installer may be running.
    """
    start = time.perf_counter()
    ready: set[str] = set()
    targets_norm = [t.lower() for t in targets]

    while True:
        for t in targets_norm:
            if t in ready:
                continue
            if translator.has_package(src_lang, t):
                ready.add(t)
        if set(targets_norm) == ready:
            break
        elapsed = time.perf_counter() - start
        if elapsed >= max_wait_s:
            break
        if verbose:
            pending = ", ".join(sorted(set(targets_norm) - ready))
            print(
                f"Waiting for Argos packages ({src_lang}->[{pending}])… {int(elapsed)}s",
                flush=True,
            )
        time.sleep(1.0)
    return ready
