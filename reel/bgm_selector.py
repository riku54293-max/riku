from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Callable

from config.settings import PipelineConfig
from reel.models import BGMSelection

AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg")

DurationFn = Callable[[Path], float]


def _default_duration_fn(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobeでBGMの尺取得に失敗しました: {path} ({result.stderr})")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def list_bgm_candidates(bgm_library_dir: Path, mood: str) -> list[Path]:
    mood_dir = bgm_library_dir / mood
    if not mood_dir.is_dir():
        raise FileNotFoundError(
            f"BGMフォルダが見つかりません: {mood_dir} "
            f"(bgm_library_dir 配下に mood名フォルダ '{mood}' を用意してください)"
        )
    candidates = sorted(
        p for p in mood_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    )
    if not candidates:
        raise FileNotFoundError(f"BGMフォルダが空です: {mood_dir}")
    return candidates


def select_bgm(
    bgm_library_dir: Path,
    mood: str,
    exclude: set[str] | None = None,
    duration_fn: DurationFn = _default_duration_fn,
    rng: random.Random | None = None,
) -> BGMSelection:
    rng = rng or random.Random()
    candidates = list_bgm_candidates(Path(bgm_library_dir), mood)

    exclude = exclude or set()
    filtered = [p for p in candidates if str(p) not in exclude]
    pool = filtered if filtered else candidates

    chosen = rng.choice(pool)
    duration = duration_fn(chosen)
    return BGMSelection(path=str(chosen), mood=mood, duration=duration)


def compute_ducking_envelope(
    bgm_duration: float,
    narration_windows: list[tuple[float, float]],
    normal_gain: float,
    duck_gain: float,
    fade: float,
) -> list[tuple[float, float]]:
    if bgm_duration <= 0:
        raise ValueError("bgm_duration は正の値である必要があります")

    breakpoints: list[tuple[float, float]] = [(0.0, normal_gain)]
    for start, end in sorted(narration_windows):
        fade_in_start = max(0.0, start - fade)
        fade_out_end = min(bgm_duration, end + fade)
        breakpoints.append((fade_in_start, normal_gain))
        breakpoints.append((min(start, fade_out_end), duck_gain))
        breakpoints.append((min(end, fade_out_end), duck_gain))
        breakpoints.append((fade_out_end, normal_gain))
    breakpoints.append((bgm_duration, normal_gain))

    deduped: list[tuple[float, float]] = []
    for t, g in breakpoints:
        t = max(0.0, min(bgm_duration, t))
        if deduped and abs(deduped[-1][0] - t) < 1e-9:
            deduped[-1] = (t, g)
        else:
            deduped.append((t, g))
    return sorted(deduped, key=lambda p: p[0])


def make_gain_function(breakpoints: list[tuple[float, float]]) -> Callable[[float], float]:
    times = [t for t, _ in breakpoints]
    gains = [g for _, g in breakpoints]

    def gain_at(t: float) -> float:
        if t <= times[0]:
            return gains[0]
        if t >= times[-1]:
            return gains[-1]
        for i in range(1, len(times)):
            if t <= times[i]:
                t0, t1 = times[i - 1], times[i]
                g0, g1 = gains[i - 1], gains[i]
                if t1 == t0:
                    return g1
                ratio = (t - t0) / (t1 - t0)
                return g0 + (g1 - g0) * ratio
        return gains[-1]

    return gain_at
