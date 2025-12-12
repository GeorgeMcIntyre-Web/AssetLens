import { describe, expect, it } from "vitest";
import { readMockBom, readMockDetections } from "./mockData";

describe("mock data loader", () => {
  it("loads sample-data expected outputs when mock mode is enabled", async () => {
    process.env.NEXT_PUBLIC_MOCK_MODE = "true";
    const detections = await readMockDetections();
    const bom = await readMockBom();

    expect(detections.schemaVersion).toBe("detections/v1");
    expect(bom.schemaVersion).toBe("bom/v1");
    expect(bom.traceId).toBe(detections.traceId);
    expect(bom.configHash).toBe(detections.configHash);
    expect(detections.renders.length).toBeGreaterThanOrEqual(1);
    expect(bom.items.length).toBeGreaterThanOrEqual(1);
  });
});

