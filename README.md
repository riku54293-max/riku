# daily_pipeline.py — 中高生向けリール自動生成

Claude API + VOICEPEAK連携の日次コンテンツパイプラインを拡張し、
Instagram/TikTokリール動画（9:16, 30〜60秒）を自動生成します。

## ディレクトリ構成

```
.
├── daily_pipeline.py          # CLIエントリポイント（daily / reel サブコマンド）
├── config/
│   ├── settings.py            # PipelineConfig（パス・数値パラメータを一元管理）
│   └── SNS運用マスタープロンプト.md  # ペルソナ定義（叩き台。中身だけ差し替え可）
├── reel/
│   ├── models.py               # Phrase / PhraseSet / TimedPhrase / BGMSelection
│   ├── phrase_generator.py     # Claude API: 3幕構成フレーズをJSON生成
│   ├── voice_synth.py          # VOICEPEAK: ナレーション合成 + 表示タイミング算出
│   ├── bgm_selector.py         # BGM選定 + ダッキング音量エンベロープ計算
│   └── video_composer.py       # moviepy: Ken Burns + テロップ + 音声合成
├── output/reels/                # 出力先 {日付}_{フレーズID}.mp4
├── assets_example/              # 素材フォルダのサンプル構成（実素材はご自身で配置）
│   ├── bgm/{energetic,calm,emotional,upbeat}/
│   └── images/
└── tests/                       # 純粋ロジックのユニットテスト
```

## パイプラインの流れ

1. **phrase_generator** — `SNS運用マスタープロンプト.md` のペルソナ + お題を渡し、
   Claude APIで `hook → develop → landing` の3幕構成フレーズをJSONで取得・検証。
2. **voice_synth** — フレーズごとにVOICEPEAK CLIでナレーションwavを合成し、
   各フレーズの表示開始/終了時刻（テロップタイミング）を算出、無音区間を挟んで結合。
3. **bgm_selector** — `bgm_library_dir/{mood}/` からmoodに合うBGMをランダム選定し、
   ナレーション区間だけ音量を下げるダッキング用の音量エンベロープを計算。
4. **video_composer** — 背景画像にKen Burns効果を適用し、フェードイン式テロップ・
   ナレーション・ダッキングBGMを合成して1080×1920のmp4を出力。

## 使い方

```bash
pip install -r requirements.txt
# 別途: ffmpeg / ffprobe と VOICEPEAK本体のインストールが必要

export ANTHROPIC_API_KEY=sk-...
export VOICEPEAK_PATH=/path/to/voicepeak
export VOICEPEAK_NARRATOR="キャラクター名"

python daily_pipeline.py reel \
  --topic "定期テスト前の焦り" \
  --bgm-dir /path/to/your/bgm_library \
  --images-dir /path/to/your/background_images \
  --output-dir output/reels
```

- `--bgm-dir` は `energetic/ calm/ emotional/ upbeat/` のmood別サブフォルダを想定
  （`config/settings.py` の `MOOD_CHOICES` と一致させてください）。
- `--images-dir` 内の画像は複数枚まで対応し、動画の長さに応じて均等に配分されます。
- `--persona-prompt` で `SNS運用マスタープロンプト.md` の実ファイルに差し替え可能です。

## テスト

外部サービス（Claude API / VOICEPEAK / ffmpeg）に依存しない純粋ロジック部分のみ、
このリポジトリ内で実行できます。

```bash
python -m unittest discover -s tests -v
```

## 既知の制約 / 未検証事項

このセッションの実行環境には `numpy` / `Pillow` / `moviepy` / `anthropic` の各パッケージ、
および `ffmpeg` / VOICEPEAK 本体がインストールされておらず、実際の動画書き出しまでを
通しで実行検証することはできていません（PyPIへのネットワークアクセスも不可でした）。
`reel/video_composer.py` はこれらのライブラリを遅延importする設計にしてあるため、
未インストールでも純粋ロジック（フレーズ検証・タイミング計算・ダッキング計算・
出力パス組み立てなど）はテスト可能です。実素材とVOICEPEAK・ffmpegが揃った環境で、
一度エンドツーエンドの動作確認をお願いします。
