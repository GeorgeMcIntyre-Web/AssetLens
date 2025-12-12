import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export type Box = { x: number; y: number; w: number; h: number };

export type Detection = {
  id: string;
  label: string;
  scoreBps: number;
  box: Box;
};

export type RenderDetections = {
  file: string;
  imageSha256: string;
  width: number;
  height: number;
  detections: Detection[];
};

export type DetectionsOutput = {
  schemaVersion: string;
  traceId: string;
  configHash: string;
  seed: number;
  renders: RenderDetections[];
};

export type BomItem = { label: string; count: number };
export type BomOutput = {
  schemaVersion: string;
  traceId: string;
  configHash: string;
  items: BomItem[];
};

function requireMockModeEnabled() {
  if (process.env.NEXT_PUBLIC_MOCK_MODE !== "true") {
    throw new Error(
      "Mock mode is disabled. Set NEXT_PUBLIC_MOCK_MODE=true to load sample-data expected outputs.",
    );
  }
}

function sampleDataPath(...parts: string[]) {
  // Repo-root anchored so it works regardless of cwd (apps/web, repo root, etc).
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const repoRoot = path.resolve(__dirname, "../../../../");
  return path.resolve(repoRoot, "sample-data", ...parts);
}

export async function readMockDetections(): Promise<DetectionsOutput> {
  requireMockModeEnabled();
  const p = sampleDataPath("expected", "detections.json");
  return JSON.parse(await readFile(p, "utf8")) as DetectionsOutput;
}

export async function readMockBom(): Promise<BomOutput> {
  requireMockModeEnabled();
  const p = sampleDataPath("expected", "bom.json");
  return JSON.parse(await readFile(p, "utf8")) as BomOutput;
}

