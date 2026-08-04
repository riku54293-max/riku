import sharp from "sharp";
import { randomUUID } from "crypto";

/**
 * 生成画像の出所証明のための透かし処理。
 * 1. 可視の半透明ウォーターマークを右下に合成(悪用・なりすまし利用への抑止力)
 * 2. AI生成であることを示すメタデータ(Software/ImageDescription)とコンテンツIDを付与
 *
 * 注: 完全な不可視電子透かし(周波数領域への埋め込み等)は追加のライブラリが必要になるため、
 * まずは実装コストが低く効果が明確なこの2点を実装している。
 */

export interface WatermarkedImage {
  buffer: Buffer;
  contentId: string;
}

function buildWatermarkSvg(width: number, height: number, label: string): Buffer {
  const fontSize = Math.max(14, Math.round(width * 0.025));
  const padding = Math.round(fontSize * 0.8);
  const svg = `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <style>
        .wm { font-family: sans-serif; font-size: ${fontSize}px; fill: #ffffff; fill-opacity: 0.6; }
        .wm-shadow { font-family: sans-serif; font-size: ${fontSize}px; fill: #000000; fill-opacity: 0.35; }
      </style>
      <text x="${width - padding + 1}" y="${height - padding + 1}" text-anchor="end" class="wm-shadow">${label}</text>
      <text x="${width - padding}" y="${height - padding}" text-anchor="end" class="wm">${label}</text>
    </svg>
  `;
  return Buffer.from(svg);
}

export async function applyWatermark(
  buffer: Buffer,
  label = "AI Generated"
): Promise<WatermarkedImage> {
  const source = sharp(buffer);
  const metadata = await source.metadata();
  const width = metadata.width ?? 1024;
  const height = metadata.height ?? 1024;
  const contentId = randomUUID();

  const watermarkedBuffer = await source
    .composite([{ input: buildWatermarkSvg(width, height, label), top: 0, left: 0 }])
    .withMetadata({
      exif: {
        IFD0: {
          Software: "CrossdressingApp AI Pipeline",
          ImageDescription: `AI-generated stylization. Content-ID: ${contentId}`,
          Artist: "CrossdressingApp",
        },
      },
    })
    .jpeg({ quality: 92 })
    .toBuffer();

  return { buffer: watermarkedBuffer, contentId };
}
