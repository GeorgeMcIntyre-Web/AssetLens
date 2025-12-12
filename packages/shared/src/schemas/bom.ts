import { z } from 'zod';

import { SCHEMA_VERSION } from './constants';
import { JobIdSchema, ProvenanceSchema, Sha256Schema, TraceIdSchema } from './common';

export const ComponentHashSchema = z
  .object({
    sha256: Sha256Schema.optional(),
    sha1: z.string().regex(/^[0-9a-f]{40}$/i).optional()
  })
  .strict();

export const BomComponentSchema = z
  .object({
    componentId: z.string().min(1),
    name: z.string().min(1),
    version: z.string().min(1).optional(),
    purl: z.string().min(1).optional(),
    licenses: z.array(z.string().min(1)).optional(),
    hashes: ComponentHashSchema.optional(),
    dependencies: z.array(z.string().min(1)).optional()
  })
  .strict();

export const BomDocumentSchema = z
  .object({
    schemaVersion: z.literal(SCHEMA_VERSION),
    traceId: TraceIdSchema,
    jobId: JobIdSchema,
    createdAt: z.string().datetime(),
    provenance: ProvenanceSchema,
    components: z.array(BomComponentSchema)
  })
  .strict();

export type BomComponent = z.infer<typeof BomComponentSchema>;
export type BomDocument = z.infer<typeof BomDocumentSchema>;
