import sharp from "sharp";

/**
 * パーソナルカラー(4シーズン)自動診断のヒューリスティック実装。
 *
 * 手順:
 *   1. 画像中央付近(顔が写っていると想定される領域)から肌色らしいピクセルをサンプリング
 *   2. 平均RGBをCIE Lab色空間に変換
 *   3. Labのa*/b*から色相角(暖色/寒色)、L*から明度(春夏系/秋冬系)を推定し4シーズンに分類
 *
 * 注意: これは学習済みモデルや実際の顔検出を使わない簡易近似であり、
 * プロのパーソナルカラー診断と同等の精度は保証しない。あくまでデフォルト値の
 * 自動提案であり、ユーザーは常に手動でシーズンを選び直せる設計にすること。
 */

export type Season = "イエベ春" | "イエベ秋" | "ブルベ夏" | "ブルベ冬";

export const SEASON_PALETTES: Record<
  Season,
  { eyeshadowPalette: string; lipColor: string; hairColor: string }
> = {
  イエベ春: {
    eyeshadowPalette: "コーラル×アイボリー",
    lipColor: "コーラルピンク",
    hairColor: "暖かみのあるブラウン",
  },
  イエベ秋: {
    eyeshadowPalette: "テラコッタ×ブラウン",
    lipColor: "ブリックレッド",
    hairColor: "カーキブラウン",
  },
  ブルベ夏: {
    eyeshadowPalette: "ラベンダー×グレージュ",
    lipColor: "ローズピンク",
    hairColor: "アッシュブラウン",
  },
  ブルベ冬: {
    eyeshadowPalette: "モノトーン×ボルドー",
    lipColor: "ボルドーレッド",
    hairColor: "ダークアッシュ",
  },
};

export interface PersonalColorEstimate {
  season: Season;
  confidence: number; // 0-1。ヒューリスティックのため最大でも0.6程度に留める
}

function isSkinPixel(r: number, g: number, b: number): boolean {
  // Peer et al. のRGBベース肌色検出ルール(照明変化にある程度頑健な古典的近似)
  const maxC = Math.max(r, g, b);
  const minC = Math.min(r, g, b);
  return (
    r > 95 &&
    g > 40 &&
    b > 20 &&
    maxC - minC > 15 &&
    Math.abs(r - g) > 15 &&
    r > g &&
    r > b
  );
}

function srgbToLinear(c: number): number {
  const v = c / 255;
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

function labF(t: number): number {
  const delta = 6 / 29;
  return t > delta ** 3 ? Math.cbrt(t) : t / (3 * delta ** 2) + 4 / 29;
}

function rgbToLab(r: number, g: number, b: number): { L: number; a: number; b: number } {
  const rl = srgbToLinear(r);
  const gl = srgbToLinear(g);
  const bl = srgbToLinear(b);

  const x = (0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl) * 100;
  const y = (0.2126729 * rl + 0.7151522 * gl + 0.072175 * bl) * 100;
  const z = (0.0193339 * rl + 0.119192 * gl + 0.9503041 * bl) * 100;

  const xn = 95.047;
  const yn = 100.0;
  const zn = 108.883;

  const fx = labF(x / xn);
  const fy = labF(y / yn);
  const fz = labF(z / zn);

  return {
    L: 116 * fy - 16,
    a: 500 * (fx - fy),
    b: 200 * (fy - fz),
  };
}

export async function estimatePersonalColor(imageBuffer: Buffer): Promise<PersonalColorEstimate> {
  const size = 128;
  const { data, info } = await sharp(imageBuffer)
    .resize(size, size, { fit: "cover" })
    .raw()
    .toBuffer({ resolveWithObject: true });

  const channels = info.channels;
  // 縦長ポートレート写真を想定し、顔が写りやすい中央〜やや上寄りの領域をサンプリング
  const xStart = Math.floor(size * 0.3);
  const xEnd = Math.floor(size * 0.7);
  const yStart = Math.floor(size * 0.15);
  const yEnd = Math.floor(size * 0.55);

  let count = 0;
  let rSum = 0;
  let gSum = 0;
  let bSum = 0;

  for (let y = yStart; y < yEnd; y++) {
    for (let x = xStart; x < xEnd; x++) {
      const idx = (y * size + x) * channels;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      if (isSkinPixel(r, g, b)) {
        rSum += r;
        gSum += g;
        bSum += b;
        count++;
      }
    }
  }

  const sampledArea = (xEnd - xStart) * (yEnd - yStart);

  if (count === 0) {
    // 肌色ピクセルを検出できなかった場合は最も無難な中立値を信頼度0で返す
    return { season: "イエベ春", confidence: 0 };
  }

  const avgR = rSum / count;
  const avgG = gSum / count;
  const avgB = bSum / count;
  const lab = rgbToLab(avgR, avgG, avgB);

  const hueAngleDeg = (Math.atan2(lab.b, lab.a) * 180) / Math.PI;
  const isWarm = hueAngleDeg > 55; // 経験的な閾値。黄み方向が強いほど暖色(イエベ)寄りと近似
  const isBright = lab.L > 62; // 明度で春夏系/秋冬系を近似的に分岐

  let season: Season;
  if (isWarm && isBright) season = "イエベ春";
  else if (isWarm && !isBright) season = "イエベ秋";
  else if (!isWarm && isBright) season = "ブルベ夏";
  else season = "ブルベ冬";

  const coverageRatio = count / sampledArea;
  const confidence = Math.min(0.6, coverageRatio); // ヒューリスティックのため上限0.6

  return { season, confidence };
}
