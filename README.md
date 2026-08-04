# 女装トランスフォーメーションアプリ（プロンプト設計プロジェクト）

男性が顔写真をアップロードすると、プロのメイクアップアーティスト・ヘアメイクアーティスト・
パーソナルカラーアナリスト・ファッションスタイリストの視点を統合したAIが、自然な
「女性的スタイリング変換」を施した画像を生成するアプリのための設計ドキュメント一式です。

## ドキュメント構成

- [`prompts/transformation_prompt.md`](prompts/transformation_prompt.md)
  画像生成AIに渡すシステムプロンプト本体。メイク・ヘア・色彩・スタイリングの
  4つのプロ視点ごとに詳細項目を整理し、動的パラメータで個人ごとに出し分けられる設計。
- [`docs/security-firewall.md`](docs/security-firewall.md)
  アップロード画像のマルウェア対策（ファイアウォール設計）と、プロンプト／ノウハウが
  模倣されにくくするための多層防御設計。倫理・プライバシーガードレールも含む。

## 設計方針

- **本人性の保持**：骨格・目鼻立ちは変えず、メイクとスタイリングのみを変換する
  （別人化・年齢変化・体型の誇張はしない）
- **多段パイプライン**：単一プロンプトではなく「顔分析 → パーソナルカラー診断 →
  メイク生成 → ヘア生成 → スタイリング生成」の複数ステップに分割し、模倣コストを高める
- **同意ベースの運用**：本人写真のみアップロード可、未成年保護、生成画像への透かし付与など
  倫理面のガードレールを技術対策と同格で扱う

## プロジェクト構成

- `backend/` — Express + TypeScript製API。アップロード検証→隔離保存→マルウェアスキャン→
  EXIF除去/再エンコード→プロンプト構築→Gemini画像生成、のセキュリティパイプラインを実装
- `mobile/` — Expo (React Native + TypeScript) 製スマホアプリ。写真選択→スタイル選択→
  結果表示の3画面構成
- `docs/security-firewall.md` — セキュリティ設計の詳細
- `prompts/transformation_prompt.md` — AIプロンプトの詳細設計（`backend/src/pipeline/buildPrompt.ts` に実装として反映済み）

## セットアップ

### ClamAV（マルウェアスキャン）

```bash
docker compose up -d clamav
```

初回起動時はウイルス定義DB（freshclam）のダウンロードに数分かかります。
`docker compose ps` で `healthy` になってからバックエンドを起動してください。
`CLAMAV_HOST` を設定しない場合、バックエンドはヒューリスティックスキャンのみで動作します
（本番運用では非推奨。詳細は [`docs/security-firewall.md`](docs/security-firewall.md) 参照）。

### バックエンド

```bash
cd backend
npm install
cp .env.example .env   # GEMINI_API_KEY を設定（CLAMAV_HOST はデフォルトで localhost）
npm run dev
```

### モバイルアプリ

```bash
cd mobile
npm install
cp .env.example .env   # EXPO_PUBLIC_API_BASE_URL をバックエンドのURLに設定
npx expo install --fix # Expo SDKと依存バージョンを実行環境に合わせて調整
npm start
```

> **注記**：本セッションの開発環境ではnpmレジストリへのアクセスが制限されており、
> `npm install` によるビルド検証は実施できていません。ローカル環境で `npm install` /
> `npm run typecheck` を実行して依存関係とビルドを確認してください。

## 今後の実装候補

- より強固な電子透かし（周波数領域埋め込み等）への強化
  - 現状は `backend/src/pipeline/watermark.ts` で可視ウォーターマーク＋AI生成メタデータ付与を実装済み
- 同意フローの内容の法務レビュー（現状は `mobile/src/screens/ConsentScreen.tsx` で
  「本人写真のみ」「18歳以上」の同意チェックをアプリ起動時に必須化する簡易実装。
  実際の利用規約・法的文言としての妥当性は法務担当者による確認が必要）
- パーソナルカラー自動診断の精度向上（現状は `backend/src/pipeline/personalColor.ts` で
  肌色ピクセルのRGBヒューリスティック検出＋Lab色空間の色相角/明度による簡易4シーズン
  分類を実装済み。実際の顔検出モデルや学習済み分類器を使った精度向上が今後の課題）
