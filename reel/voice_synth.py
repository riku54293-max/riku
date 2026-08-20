from __future__ import annotations

import subprocess
import wave
from pathlib import Path
from typing import Callable

from config.settings import PipelineConfig
from reel.models import NarrationResult, PhraseSet, TimedPhrase

SynthFn = Callable[[str, Path, PipelineConfig], None]


def _default_synth_fn(text: str, out_path: Path, config: PipelineConfig) -> None:
    cmd = [
        config.voicepeak_path,
        "-s",
        text,
        "-o",
        str(out_path),
        "-n",
        config.voicepeak_narrator,
        "--speed",
        str(config.voicepeak_speed),
        "--pitch",
        str(config.voicepeak_pitch),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"VOICEPEAKでの音声合成に失敗しました (exit={result.returncode}): {result.stderr}"
        )
    if not out_path.exists():
        raise RuntimeError(f"VOICEPEAKが音声ファイルを生成しませんでした: {out_path}")


def wave_duration_sec(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def compute_timing(durations: list[float], gap: float) -> list[tuple[float, float]]:
    timings: list[tuple[float, float]] = []
    cursor = 0.0
    for duration in durations:
        start = cursor
        end = start + duration
        timings.append((start, end))
        cursor = end + gap
    return timings


def concat_wavs_with_gaps(paths: list[Path], gap: float, out_path: Path) -> float:
    if not paths:
        raise ValueError("連結対象のwavファイルがありません")

    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()

    silence_frame_count = int(gap * params.framerate)
    silence_bytes = b"\x00" * (silence_frame_count * params.sampwidth * params.nchannels)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        for i, path in enumerate(paths):
            with wave.open(str(path), "rb") as wf:
                if (wf.getframerate(), wf.getsampwidth(), wf.getnchannels()) != (
                    params.framerate,
                    params.sampwidth,
                    params.nchannels,
                ):
                    raise RuntimeError(
                        f"wavフォーマットが不一致です: {path} "
                        "(VOICEPEAKの出力設定を統一してください)"
                    )
                out.writeframes(wf.readframes(wf.getnframes()))
            if i != len(paths) - 1:
                out.writeframes(silence_bytes)

    return wave_duration_sec(out_path)


def synthesize_narration(
    phrase_set: PhraseSet,
    config: PipelineConfig,
    work_dir: Path,
    synth_fn: SynthFn = _default_synth_fn,
) -> NarrationResult:
    work_dir.mkdir(parents=True, exist_ok=True)

    audio_paths: list[Path] = []
    for phrase in phrase_set.phrases:
        out_path = work_dir / f"{phrase_set.phrase_id}_{phrase.order:02d}.wav"
        synth_fn(phrase.text, out_path, config)
        audio_paths.append(out_path)

    durations = [wave_duration_sec(p) for p in audio_paths]
    timings = compute_timing(durations, config.phrase_gap_sec)

    concatenated_path = work_dir / f"{phrase_set.phrase_id}_narration.wav"
    total_duration = concat_wavs_with_gaps(audio_paths, config.phrase_gap_sec, concatenated_path)

    timed_phrases = [
        TimedPhrase(phrase=phrase, audio_path=str(path), start=start, end=end)
        for phrase, path, (start, end) in zip(phrase_set.phrases, audio_paths, timings)
    ]

    return NarrationResult(
        timed_phrases=timed_phrases,
        concatenated_audio_path=str(concatenated_path),
        total_duration=total_duration,
    )
