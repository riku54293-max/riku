import { GoogleGenerativeAI } from "@google/generative-ai";
import { config } from "../config";

/**
 * Google Gemini 画像生成APIとの連携。
 *
 * 注意: Geminiの画像生成対応モデル名・レスポンス形式はAPIバージョンによって変わるため、
 * 本番投入前に https://ai.google.dev/gemini-api/docs/image-generation で
 * 契約中のAPIキーが利用できる最新のモデル名を確認し、GEMINI_IMAGE_MODEL を設定すること。
 *
 * 2026年2月のGoogle側ポリシー強化(通称Nano Banana 2)により、実在人物の顔・服装の
 * 入れ替えに関する安全フィルタが厳格化されている。本人の同意がある自撮り編集は
 * 許容される想定だが、モデル側の安全フィルタによって個別リクエストが拒否される
 * ケースが実運用で一定数発生し得るため、拒否理由を利用者に分かりやすく伝える
 * ためのエラー型を用意している。
 */

export class GeminiPolicyRefusalError extends Error {
  reason: string;

  constructor(reason: string) {
    super(`Geminiの安全ポリシーにより生成がブロックされました: ${reason}`);
    this.name = "GeminiPolicyRefusalError";
    this.reason = reason;
  }
}

export interface TransformImageInput {
  imageBuffer: Buffer;
  mimeType: string;
  prompt: string;
}

export interface TransformImageResult {
  imageBase64: string;
  mimeType: string;
}

export async function transformImageWithGemini(
  input: TransformImageInput
): Promise<TransformImageResult> {
  const genAI = new GoogleGenerativeAI(config.getGeminiApiKey());
  const model = genAI.getGenerativeModel({ model: config.geminiImageModel });

  const result = await model.generateContent([
    { text: input.prompt },
    {
      inlineData: {
        data: input.imageBuffer.toString("base64"),
        mimeType: input.mimeType,
      },
    },
  ]);

  // プロンプト自体が安全フィルタでブロックされた場合、候補(candidates)が
  // 一つも返らずここでblockReasonが設定される
  const blockReason = result.response.promptFeedback?.blockReason;
  if (blockReason) {
    throw new GeminiPolicyRefusalError(blockReason);
  }

  const candidate = result.response.candidates?.[0];

  // 候補は返るが、安全フィルタ等により生成が途中停止した場合はfinishReasonが
  // "STOP"以外(SAFETY / PROHIBITED_CONTENT 等)になる
  if (candidate?.finishReason && candidate.finishReason !== "STOP") {
    throw new GeminiPolicyRefusalError(candidate.finishReason);
  }

  const parts = candidate?.content?.parts ?? [];
  const imagePart = parts.find((part) => "inlineData" in part && part.inlineData);

  if (!imagePart || !("inlineData" in imagePart) || !imagePart.inlineData) {
    throw new Error(
      "Geminiから画像データが返されませんでした。GEMINI_IMAGE_MODEL の設定と、" +
        "APIキーが画像生成に対応しているか確認してください。"
    );
  }

  return {
    imageBase64: imagePart.inlineData.data,
    mimeType: imagePart.inlineData.mimeType ?? "image/jpeg",
  };
}
