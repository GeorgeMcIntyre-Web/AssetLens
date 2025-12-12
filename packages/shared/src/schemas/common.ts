import { z } from 'zod';

export const TraceIdSchema = z.string().uuid();
export const JobIdSchema = z.string().uuid();

export const Sha256Schema = z
  .string()
  .regex(/^[0-9a-f]{64}$/i, 'Expected a 64-char hex sha256');

export const CommitHashSchema = z
  .string()
  .regex(/^(UNKNOWN|[0-9a-f]{7,40})$/i, 'Expected git sha or UNKNOWN');

export const ProvenanceSchema = z
  .object({
    pipelineName: z.string().min(1),
    pipelineVersion: z.string().min(1),
    modelName: z.string().min(1),
    modelVersion: z.string().min(1),
    configHash: Sha256Schema,
    commitHash: CommitHashSchema,
    seed: z.number().int().nonnegative().optional()
  })
  .strict();

export type Provenance = z.infer<typeof ProvenanceSchema>;
