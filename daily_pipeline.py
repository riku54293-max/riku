#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import tempfile
from pathlib import Path

from config.settings import PipelineConfig
from reel import bgm_selector, phrase_generator, video_composer, voice_synth


def run_daily_content_pipeline(topic: str, config: PipelineConfig) -> str:
    """既存の日次コンテンツパイプライン（Claude APIで台本生成 + VOICEPEAKで単発音声化）。

    リール動画生成はこの下の `run_reel_pipeline` として別途拡張している。
    """
    phrase_set = phrase_generator.generate_phrases(config, topic)
    work_dir = Path(tempfile.mkdtemp(prefix="daily_content_"))
    narration = voice_synth.synthesize_narration(phrase_set, config, work_dir)
    return narration.concatenated_audio_path


def run_reel_pipeline(topic: str, config: PipelineConfig, image_paths: list[str]) -> Path:
    phrase_set = phrase_generator.generate_phrases(config, topic)

    work_dir = Path(tempfile.mkdtemp(prefix=f"reel_{phrase_set.phrase_id}_"))
    narration = voice_synth.synthesize_narration(phrase_set, config, work_dir)

    bgm = bgm_selector.select_bgm(config.bgm_library_dir, phrase_set.mood)

    date_str = dt.date.today().strftime("%Y%m%d")
    output_path = video_composer.compose_reel(
        phrase_set=phrase_set,
        narration=narration,
        bgm=bgm,
        background_image_paths=image_paths,
        config=config,
        date_str=date_str,
    )
    return output_path


def collect_images(images_dir: Path) -> list[str]:
    exts = (".jpg", ".jpeg", ".png", ".webp")
    paths = sorted(p for p in Path(images_dir).iterdir() if p.is_file() and p.suffix.lower() in exts)
    if not paths:
        raise FileNotFoundError(f"背景画像が見つかりません: {images_dir}")
    return [str(p) for p in paths]


def build_config_from_args(args: argparse.Namespace) -> PipelineConfig:
    config = PipelineConfig()
    overrides = {}
    if args.bgm_dir:
        overrides["bgm_library_dir"] = Path(args.bgm_dir)
    if args.images_dir:
        overrides["images_dir"] = Path(args.images_dir)
    if args.output_dir:
        overrides["output_dir"] = Path(args.output_dir)
    if args.persona_prompt:
        overrides["persona_prompt_path"] = Path(args.persona_prompt)
    if args.voicepeak_path:
        overrides["voicepeak_path"] = args.voicepeak_path
    if args.narrator:
        overrides["voicepeak_narrator"] = args.narrator
    return dataclasses.replace(config, **overrides)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily content / reel generation pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily", help="既存の日次コンテンツ生成（Claude+VOICEPEAK音声）")
    daily.add_argument("--topic", required=True)

    reel = subparsers.add_parser("reel", help="Instagram/TikTokリール動画(9:16, 30-60秒)を生成")
    reel.add_argument("--topic", required=True, help="今日のリールのお題・テーマ")
    reel.add_argument("--bgm-dir", required=True, help="mood別サブフォルダを持つBGMライブラリのパス")
    reel.add_argument("--images-dir", required=True, help="背景画像フォルダのパス")
    reel.add_argument("--output-dir", default=None, help="出力先 (デフォルト: output/reels)")
    reel.add_argument("--persona-prompt", default=None, help="SNS運用マスタープロンプト.mdのパス")
    reel.add_argument("--voicepeak-path", default=None, help="VOICEPEAK CLI実行ファイルのパス")
    reel.add_argument("--narrator", default=None, help="VOICEPEAKナレーターキャラ名")

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    config = build_config_from_args(args) if args.command == "reel" else PipelineConfig()

    if args.command == "daily":
        result = run_daily_content_pipeline(args.topic, config)
        print(result)
    elif args.command == "reel":
        image_paths = collect_images(config.images_dir)
        output_path = run_reel_pipeline(args.topic, config, image_paths)
        print(output_path)


if __name__ == "__main__":
    main()
