import dotenv from "dotenv";

dotenv.config();

function requireEnvAtRuntime(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `環境変数 ${name} が未設定です。.env.example を参考に .env を作成してください。`
    );
  }
  return value;
}

export const config = {
  port: Number(process.env.PORT ?? 4000),
  corsOrigin: process.env.CORS_ORIGIN ?? "*",
  maxUploadBytes: Number(process.env.MAX_UPLOAD_BYTES ?? 20 * 1024 * 1024),
  geminiImageModel: process.env.GEMINI_IMAGE_MODEL ?? "gemini-2.0-flash-exp",
  clamAvHost: process.env.CLAMAV_HOST || undefined,
  clamAvPort: Number(process.env.CLAMAV_PORT ?? 3310),
  getGeminiApiKey: () => requireEnvAtRuntime("GEMINI_API_KEY"),
};
