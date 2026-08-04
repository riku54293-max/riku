import { Router } from "express";
import multer from "multer";
import { config } from "../config";
import { validateImageFile } from "../pipeline/validateFile";
import { quarantineFile, removeQuarantinedFile } from "../pipeline/quarantine";
import { scanFile } from "../pipeline/malwareScan";
import { stripAndReencode } from "../pipeline/reencode";
import { buildTransformationPrompt, TransformationParams } from "../pipeline/buildPrompt";
import { transformImageWithGemini, GeminiPolicyRefusalError } from "../pipeline/geminiClient";
import { applyWatermark } from "../pipeline/watermark";
import { estimatePersonalColor } from "../pipeline/personalColor";
import { transformRateLimiter } from "../middleware/rateLimit";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: config.maxUploadBytes },
});

export const transformRouter = Router();

/**
 * POST /api/transform
 * multipart/form-data:
 *   - image: 写真ファイル (JPEG/PNG/HEIC)
 *   - params: TransformationParams の一部をJSON文字列で指定(省略可、省略時はデフォルト値)
 *
 * パイプライン: ファイル検証 → 隔離保存 → マルウェアスキャン → EXIF除去/再エンコード
 *              → プロンプト構築(サーバー内部のみ) → Gemini呼び出し → 隔離ファイル削除
 */
transformRouter.post("/api/transform", transformRateLimiter, upload.single("image"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "image フィールドが必要です" });
  }

  const validation = validateImageFile(req.file.buffer, config.maxUploadBytes);
  if (!validation.valid) {
    return res.status(400).json({ error: validation.reason });
  }

  const quarantined = await quarantineFile(req.file.buffer, validation.type!);

  try {
    const scanResult = await scanFile(req.file.buffer);
    if (!scanResult.clean) {
      return res.status(400).json({
        error: "アップロードされたファイルはセキュリティスキャンで拒否されました",
        detail: scanResult.reason,
      });
    }

    const reencoded = await stripAndReencode(req.file.buffer);

    let params: Partial<TransformationParams> = {};
    if (typeof req.body.params === "string" && req.body.params.length > 0) {
      try {
        params = JSON.parse(req.body.params);
      } catch {
        return res.status(400).json({ error: "params は有効なJSON文字列である必要があります" });
      }
    }

    let detectedPersonalColor: { season: string; confidence: number } | undefined;
    if (!params.undertone) {
      const estimate = await estimatePersonalColor(reencoded.buffer);
      params.undertone = estimate.season;
      detectedPersonalColor = { season: estimate.season, confidence: estimate.confidence };
    }

    const prompt = buildTransformationPrompt(params);

    const result = await transformImageWithGemini({
      imageBuffer: reencoded.buffer,
      mimeType: reencoded.mimeType,
      prompt,
    });

    const watermarked = await applyWatermark(Buffer.from(result.imageBase64, "base64"));

    return res.json({
      image: `data:image/jpeg;base64,${watermarked.buffer.toString("base64")}`,
      contentId: watermarked.contentId,
      detectedPersonalColor,
    });
  } catch (error) {
    if (error instanceof GeminiPolicyRefusalError) {
      // eslint-disable-next-line no-console
      console.warn("Gemini policy refusal:", error.reason);
      return res.status(422).json({
        error:
          "AIの安全ポリシーにより、この写真の変換はリクエストできませんでした。" +
          "別の写真や設定でお試しください。",
        code: "POLICY_REFUSED",
        reason: error.reason,
      });
    }
    // eslint-disable-next-line no-console
    console.error("transform pipeline error:", error);
    return res.status(500).json({ error: "画像変換中にエラーが発生しました" });
  } finally {
    await removeQuarantinedFile(quarantined.filePath);
  }
});
