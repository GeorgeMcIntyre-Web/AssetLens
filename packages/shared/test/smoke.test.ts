import { describe, expect, it } from "vitest";
import { SCHEMA_PLACEHOLDER } from "../src/schemas";

describe("shared smoke", () => {
  it("exports", () => {
    expect(SCHEMA_PLACEHOLDER).toBe("shared-schemas");
  });
});
