from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MOOD_CHOICES = ("energetic", "calm", "emotional", "upbeat")

DEFAULT_PERSONA_PROMPT_PATH = REPO_ROOT / "config" / "SNS運用マスタープロンプト.md"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "reels"

DEFAULT_VIDEO_SIZE = (1080, 1920)
DEFAULT_FPS = 30
DEFAULT_MIN_DURATION_SEC = 30.0
DEFAULT_MAX_DURATION_SEC = 60.0
DEFAULT_PHRASE_GAP_SEC = 0.35
DEFAULT_BGM_DUCK_GAIN = 0.22
DEFAULT_BGM_NORMAL_GAIN = 0.9
DEFAULT_BGM_DUCK_FADE_SEC = 0.4
DEFAULT_TELOP_FADE_SEC = 0.25
DEFAULT_KEN_BURNS_ZOOM = 1.15


@dataclass
class PipelineConfig:
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"))
    persona_prompt_path: Path = DEFAULT_PERSONA_PROMPT_PATH

    voicepeak_path: str = field(default_factory=lambda: os.environ.get("VOICEPEAK_PATH", "voicepeak"))
    voicepeak_narrator: str = field(default_factory=lambda: os.environ.get("VOICEPEAK_NARRATOR", "Japanese Narrator"))
    voicepeak_speed: int = 100
    voicepeak_pitch: int = 0

    # ユーザーが用意する素材フォルダ（mood別サブフォルダを持つBGMライブラリ、背景画像フォルダ）
    bgm_library_dir: Path = field(default_factory=lambda: Path(os.environ.get("BGM_LIBRARY_DIR", "")))
    images_dir: Path = field(default_factory=lambda: Path(os.environ.get("IMAGES_DIR", "")))

    output_dir: Path = DEFAULT_OUTPUT_DIR

    video_size: tuple[int, int] = DEFAULT_VIDEO_SIZE
    fps: int = DEFAULT_FPS
    min_duration_sec: float = DEFAULT_MIN_DURATION_SEC
    max_duration_sec: float = DEFAULT_MAX_DURATION_SEC
    phrase_gap_sec: float = DEFAULT_PHRASE_GAP_SEC

    bgm_duck_gain: float = DEFAULT_BGM_DUCK_GAIN
    bgm_normal_gain: float = DEFAULT_BGM_NORMAL_GAIN
    bgm_duck_fade_sec: float = DEFAULT_BGM_DUCK_FADE_SEC

    telop_fade_sec: float = DEFAULT_TELOP_FADE_SEC
    ken_burns_zoom: float = DEFAULT_KEN_BURNS_ZOOM

    font_path: str | None = field(default_factory=lambda: os.environ.get("REEL_FONT_PATH"))
