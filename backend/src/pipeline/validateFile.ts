/**
 * アップロードファイルの種別を「拡張子」ではなく「マジックバイト（ファイル先頭シグネチャ）」で検証する。
 * 拡張子だけの判定は容易に偽装できるため、ファイアウォール設計の第2層として必須。
 */

export type DetectedImageType = "jpeg" | "png" | "heic";

export interface ValidationResult {
  valid: boolean;
  type?: DetectedImageType;
  reason?: string;
}

const JPEG_SIGNATURE = [0xff, 0xd8, 0xff];
const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const HEIC_BRANDS = ["heic", "heix", "hevc", "hevx", "mif1", "msf1"];

function matchesSignature(buffer: Buffer, signature: number[]): boolean {
  if (buffer.length < signature.length) return false;
  return signature.every((byte, index) => buffer[index] === byte);
}

function detectHeic(buffer: Buffer): boolean {
  if (buffer.length < 12) return false;
  const boxType = buffer.subarray(4, 8).toString("ascii");
  if (boxType !== "ftyp") return false;
  const brand = buffer.subarray(8, 12).toString("ascii").toLowerCase();
  return HEIC_BRANDS.includes(brand);
}

export function validateImageFile(buffer: Buffer, maxBytes: number): ValidationResult {
  if (buffer.length === 0) {
    return { valid: false, reason: "空のファイルです" };
  }
  if (buffer.length > maxBytes) {
    return { valid: false, reason: `ファイルサイズが上限（${maxBytes}バイト）を超えています` };
  }

  if (matchesSignature(buffer, JPEG_SIGNATURE)) {
    return { valid: true, type: "jpeg" };
  }
  if (matchesSignature(buffer, PNG_SIGNATURE)) {
    return { valid: true, type: "png" };
  }
  if (detectHeic(buffer)) {
    return { valid: true, type: "heic" };
  }

  return {
    valid: false,
    reason: "JPEG / PNG / HEIC 以外のファイル形式は許可されていません",
  };
}
