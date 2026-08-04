import sharp from "sharp";

/**
 * 画像の再構築（ファイアウォール設計の第6層・最重要）。
 * 元ファイルを直接扱わず、ピクセルデータのみをデコードして新規JPEGとして
 * 再エンコードする。これによりEXIF（位置情報等）やファイル内に埋め込まれた
 * 不正なメタデータ・ポリグロット構造を丸ごと破棄できる。
 */

const MAX_DIMENSION = 2048;

export interface ReencodedImage {
  buffer: Buffer;
  width: number;
  height: number;
  mimeType: "image/jpeg";
}

export async function stripAndReencode(buffer: Buffer): Promise<ReencodedImage> {
  const pipeline = sharp(buffer, { failOn: "error" }).rotate(); // rotate()はEXIF Orientationを反映してからメタデータを破棄する

  const resized = pipeline.resize({
    width: MAX_DIMENSION,
    height: MAX_DIMENSION,
    fit: "inside",
    withoutEnlargement: true,
  });

  // .jpeg() はデフォルトでEXIF/ICC等のメタデータを引き継がない（withMetadata()を呼ばない限り破棄される）
  const outputBuffer = await resized.jpeg({ quality: 90, mozjpeg: true }).toBuffer();
  const metadata = await sharp(outputBuffer).metadata();

  return {
    buffer: outputBuffer,
    width: metadata.width ?? 0,
    height: metadata.height ?? 0,
    mimeType: "image/jpeg",
  };
}
