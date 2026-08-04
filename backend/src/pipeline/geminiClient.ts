import { GoogleGenerativeAI } from "@google/generative-ai";
import { config } from "../config";

/**
 * Google Gemini 画像生成APIとの連携。
 *
 * 注意: Geminiの画像生成対応モデル名・レスポンス形式はAPIバージョンによって変わるため、
 * 本番投入前に https://ai.google.dev/gemini-api/docs/image-generation で
 * 契約中のAPIキーが利用できる最新のモデル名を確認し、GEMINI_IMAGE_MODEL を設定すること。
 */

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

  const parts = result.response.candidates?.[0]?.content?.parts ?? [];
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
