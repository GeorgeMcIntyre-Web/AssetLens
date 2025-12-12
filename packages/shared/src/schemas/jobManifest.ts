import { z } from 'zod';

import { SCHEMA_VERSION } from './constants';
import { JobIdSchema, ProvenanceSchema, Sha256Schema, TraceIdSchema } from './common';

export const JobInputSchema = z
  .object({
    uri: z.string().min(1),
    sha256: Sha256Schema.optional()
  })
  .strict();

export const JobOptionsSchema = z
  .object({
    seed: z.number().int().nonnegative().optional()
  })
  .strict();

export const JobManifestSchema = z
  .object({
    schemaVersion: z.literal(SCHEMA_VERSION),
    traceId: TraceIdSchema,
    jobId: JobIdSchema,
    createdAt: z.string().datetime(),
    provenance: ProvenanceSchema,
    input: JobInputSchema,
    options: JobOptionsSchema.optional()
  })
  .strict();

export type JobManifest = z.infer<typeof JobManifestSchema>;
