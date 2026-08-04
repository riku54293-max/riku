import rateLimit from "express-rate-limit";

/**
 * 連続アップロード攻撃・API濫用対策のレート制限。
 * 画像変換はコスト・処理負荷が高いエンドポイントのため、一般的なAPIより厳しめに設定。
 */
export const transformRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "リクエストが多すぎます。しばらく待ってから再度お試しください。" },
});
