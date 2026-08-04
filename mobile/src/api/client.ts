import { DetectedPersonalColor, TransformationParams } from "../types";

// Expo は EXPO_PUBLIC_ プレフィックスの環境変数をビルド時に自動でバンドルする。
// mobile/.env に EXPO_PUBLIC_API_BASE_URL=http://<バックエンドのIP>:4000 を設定すること。
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

export interface TransformResponse {
  image: string; // data:image/jpeg;base64,... 形式
  contentId: string; // 生成画像に埋め込まれたコンテンツID(メタデータと一致)
  detectedPersonalColor?: DetectedPersonalColor; // undertone未指定時のみAIが自動診断した結果
}

export async function transformPhoto(
  photoUri: string,
  params: Partial<TransformationParams>
): Promise<TransformResponse> {
  const formData = new FormData();

  formData.append("image", {
    uri: photoUri,
    name: "photo.jpg",
    type: "image/jpeg",
  } as unknown as Blob);
  formData.append("params", JSON.stringify(params));

  const response = await fetch(`${API_BASE_URL}/api/transform`, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorBody.error ?? "画像変換に失敗しました");
  }

  const data: TransformResponse = await response.json();
  return data;
}
