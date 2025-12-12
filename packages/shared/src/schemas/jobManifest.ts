import { z } from "zod";

export const RenderInputSchema = z.object({
  /**
   * Path relative to the repo root (or job directory) so filenames remain stable across machines.
   * Example: "renders/render_0001.png"
   */
  file: z.string().min(1),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
});

export const PipelineConfigSchema = z.object({
  /**
   * Logical engine identifier. Used as part of deterministic config hashing.
   */
  engine: z.string().min(1),
  model: z.string().min(1),
  /** Score threshold expressed in basis points (0-10000). */
  scoreThresholdBps: z.number().int().min(0).max(10000),
  /** NMS threshold expressed in basis points (0-10000). */
  nmsThresholdBps: z.number().int().min(0).max(10000),
  maxDetectionsPerImage: z.number().int().min(1).max(1000),

  /**
   * Documentation fields (strings) describing how deterministic values are derived.
   * These are kept in the manifest to make "how do we reproduce this output?" explicit.
   */
  configHashAlgorithm: z.string().min(1),
  seedAlgorithm: z.string().min(1),
});

/**
 * JobManifest schema for deterministic pipeline runs.
 *
 * This is intentionally minimal for the PoC: it contains only what the backend needs
 * to derive deterministic seed/configHash and to find/interpret inputs.
 */
export const JobManifestSchema = z.object({
  schemaVersion: z.literal("job-manifest/v1"),
  traceId: z.string().min(1),
  pipeline: PipelineConfigSchema,
  inputs: z.object({
    renders: z.array(RenderInputSchema).min(1),
  }),
});

export type JobManifest = z.infer<typeof JobManifestSchema>;
