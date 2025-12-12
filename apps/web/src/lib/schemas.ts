import { z } from 'zod';

export const JobStatusSchema = z.enum(['created', 'running', 'completed', 'failed']);

export const JobSummarySchema = z.object({
  id: z.string().min(1),
  status: JobStatusSchema,
  createdAt: z.string().min(1),
});

export const JobsListSchema = z.array(JobSummarySchema);

export const DetectionSchema = z.object({
  id: z.string().min(1),
  assetType: z.string().min(1),
  confidence: z.number().min(0).max(1),
  bbox: z.tuple([z.number(), z.number(), z.number(), z.number()]),
});

export const RenderSchema = z.object({
  id: z.string().min(1),
  imagePath: z.string().min(1),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  detections: z.array(DetectionSchema),
});

export const JobDetailSchema = z.object({
  id: z.string().min(1),
  status: JobStatusSchema,
  createdAt: z.string().min(1),
  job: z.record(z.unknown()),
  renders: z.array(RenderSchema),
});

export const ReviewInstanceSchema = z.object({
  detectionId: z.string().min(1),
  accepted: z.boolean().nullable().optional(),
  relabelAssetType: z.string().min(1).nullable().optional(),
});

export const ReviewPayloadSchema = z.object({
  jobId: z.string().min(1),
  updatedAt: z.string().min(1),
  instances: z.array(ReviewInstanceSchema),
});

export type JobStatus = z.infer<typeof JobStatusSchema>;
export type JobSummary = z.infer<typeof JobSummarySchema>;
export type Detection = z.infer<typeof DetectionSchema>;
export type Render = z.infer<typeof RenderSchema>;
export type JobDetail = z.infer<typeof JobDetailSchema>;
export type ReviewInstance = z.infer<typeof ReviewInstanceSchema>;
export type ReviewPayload = z.infer<typeof ReviewPayloadSchema>;
