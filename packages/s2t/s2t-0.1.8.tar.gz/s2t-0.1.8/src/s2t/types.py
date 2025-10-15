from __future__ import annotations

from typing import TypedDict


class SegmentDict(TypedDict, total=False):
    start: float
    end: float
    text: str


class TranscriptionResult(TypedDict, total=False):
    text: str
    segments: list[SegmentDict]
    # Optional: Whisper-detected language code (e.g., 'de', 'en')
    language: str
