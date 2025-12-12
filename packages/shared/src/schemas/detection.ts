import { z } from 'zod';

import { SCHEMA_VERSION } from './constants';
import { JobIdSchema, ProvenanceSchema, Sha256Schema, TraceIdSchema } from './common';

export const DetectionSchema = z
  .object({
    detectionId: z.string().uuid(),
    kind: z.string().min(1),
    assetUri: z.string().min(1),
    assetSha256: Sha256Schema.optional(),
    score: z.number().min(0).max(1),
    metadata: z.record(z.unknown()).optional()
  })
  .strict();

export const DetectionsDocumentSchema = z
  .object({
    schemaVersion: z.literal(SCHEMA_VERSION),
    traceId: TraceIdSchema,
    jobId: JobIdSchema,
    createdAt: z.string().datetime(),
    provenance: ProvenanceSchema,
    detections: z.array(DetectionSchema)
  })
  .strict();

export type Detection = z.infer<typeof DetectionSchema>;
export type DetectionsDocument = z.infer<typeof DetectionsDocumentSchema>;
