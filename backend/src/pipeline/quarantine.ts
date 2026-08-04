import { promises as fs } from "fs";
import path from "path";
import { v4 as uuidv4 } from "uuid";

/**
 * アップロード直後のファイルは本番処理領域に触れさせず、
 * 隔離ディレクトリに一時保存してからスキャンを行う（ファイアウォール設計の第4層）。
 */

const QUARANTINE_DIR = path.join(__dirname, "..", "..", "tmp", "quarantine");

export interface QuarantinedFile {
  id: string;
  filePath: string;
}

export async function quarantineFile(buffer: Buffer, extension: string): Promise<QuarantinedFile> {
  await fs.mkdir(QUARANTINE_DIR, { recursive: true });
  const id = uuidv4();
  const filePath = path.join(QUARANTINE_DIR, `${id}.${extension}`);
  await fs.writeFile(filePath, buffer, { mode: 0o600 });
  return { id, filePath };
}

export async function removeQuarantinedFile(filePath: string): Promise<void> {
  await fs.rm(filePath, { force: true });
}
