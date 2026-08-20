from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Act(str, Enum):
    HOOK = "hook"
    DEVELOP = "develop"
    LANDING = "landing"


@dataclass
class Phrase:
    act: Act
    text: str
    order: int


@dataclass
class PhraseSet:
    phrase_id: str
    theme: str
    mood: str
    phrases: list[Phrase]
    cta: str | None = None


@dataclass
class TimedPhrase:
    phrase: Phrase
    audio_path: str
    start: float
    end: float


@dataclass
class NarrationResult:
    timed_phrases: list[TimedPhrase]
    concatenated_audio_path: str
    total_duration: float


@dataclass
class BGMSelection:
    path: str
    mood: str
    duration: float
