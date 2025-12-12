import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { JobManifestSchema } from "../src/schemas";

describe("shared smoke", () => {
  it("validates sample-data/job.json", async () => {
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const jobPath = path.resolve(__dirname, "../../../sample-data/job.json");
    const job = JSON.parse(await readFile(jobPath, "utf8")) as unknown;
    const parsed = JobManifestSchema.safeParse(job);
    expect(parsed.success).toBe(true);
  });
});
