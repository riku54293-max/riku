import express from "express";
import cors from "cors";
import { config } from "./config";
import { transformRouter } from "./routes/transform";

const app = express();

app.use(
  cors({
    origin: config.corsOrigin === "*" ? true : config.corsOrigin.split(","),
  })
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use(transformRouter);

// エラーハンドラ(multerのファイルサイズ超過等を含む)
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  // eslint-disable-next-line no-console
  console.error(err);
  res.status(400).json({ error: err.message ?? "リクエストの処理に失敗しました" });
});

app.listen(config.port, () => {
  // eslint-disable-next-line no-console
  console.log(`crossdressing-app-backend listening on port ${config.port}`);
});
