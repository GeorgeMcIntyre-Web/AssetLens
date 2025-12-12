import { isMockMode } from '@/lib/env';
import { buildBomRows } from '@/lib/bom';
import {
  JobDetailSchema,
  JobsListSchema,
  JobSummarySchema,
  ReviewPayloadSchema,
  type JobDetail,
  type JobSummary,
  type ReviewPayload,
} from '@/lib/schemas';
import { expectedJobDetail, expectedJobs } from '@/lib/mockData';
import { validateOrThrow } from '@/lib/validate';

function mockStorageGet<T>(key: string): T | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function mockStorageSet(key: string, value: unknown): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

export async function listJobs(): Promise<JobSummary[]> {
  if (isMockMode()) {
    const seed = expectedJobs();
    const extra = mockStorageGet<JobSummary[]>('mock:jobs') ?? [];
    const merged = [...seed, ...extra];

    const byId = new Map<string, JobSummary>();
    for (const j of merged) {
      byId.set(j.id, j);
    }

    return Array.from(byId.values()).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  const res = await fetch(`/api/jobs`, { cache: 'no-store' });
  if (!res.ok) {
    return [];
  }

  const json = (await res.json()) as unknown;
  return validateOrThrow(JobsListSchema, json);
}

export async function createJob(payload: {
  jobFile: File;
  renderFiles: File[];
}): Promise<JobSummary> {
  if (isMockMode()) {
    const id = `job_mock_${Date.now()}`;
    const createdAt = new Date().toISOString();
    const summary = validateOrThrow(JobSummarySchema, { id, status: 'created', createdAt });

    const jobs = mockStorageGet<JobSummary[]>('mock:jobs') ?? [];
    mockStorageSet('mock:jobs', [summary, ...jobs]);

    // Store a minimal JobDetail, using the placeholder mock render.
    const detail: JobDetail = {
      ...expectedJobDetail('job_mock_1'),
      id,
      status: 'created',
      createdAt,
      job: { filename: payload.jobFile.name },
    };

    mockStorageSet(`mock:job:${id}`, detail);
    return summary;
  }

  const fd = new FormData();
  fd.append('job', payload.jobFile);

  for (const f of payload.renderFiles) {
    fd.append('renders', f);
  }

  const res = await fetch(`/api/jobs`, { method: 'POST', body: fd });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'failed to create job');
  }

  const json = (await res.json()) as unknown;
  return validateOrThrow(JobSummarySchema, json);
}

export async function runPipeline(jobId: string): Promise<JobSummary> {
  if (isMockMode()) {
    const jobs = mockStorageGet<JobSummary[]>('mock:jobs') ?? [];
    const target = jobs.find((j) => j.id === jobId);
    if (!target) {
      return validateOrThrow(JobSummarySchema, { id: jobId, status: 'completed', createdAt: new Date().toISOString() });
    }

    const updated = { ...target, status: 'completed' as const };
    mockStorageSet(
      'mock:jobs',
      jobs.map((j) => (j.id === jobId ? updated : j)),
    );

    const detail = mockStorageGet<JobDetail>(`mock:job:${jobId}`);
    if (detail) {
      mockStorageSet(`mock:job:${jobId}`, { ...detail, status: 'completed' });
    }

    return updated;
  }

  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/run`, { method: 'POST' });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'failed to run pipeline');
  }

  const json = (await res.json()) as unknown;
  return validateOrThrow(JobSummarySchema, json);
}

export async function getJobDetail(jobId: string): Promise<JobDetail> {
  if (isMockMode()) {
    const local = mockStorageGet<JobDetail>(`mock:job:${jobId}`);
    if (local) {
      return validateOrThrow(JobDetailSchema, local);
    }

    return expectedJobDetail(jobId);
  }

  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`, { cache: 'no-store' });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'job not found');
  }

  const json = (await res.json()) as unknown;
  return validateOrThrow(JobDetailSchema, json);
}

export async function getReview(jobId: string): Promise<ReviewPayload | null> {
  if (isMockMode()) {
    const v = mockStorageGet<ReviewPayload>(`review:${jobId}`);
    if (!v) {
      return null;
    }
    return validateOrThrow(ReviewPayloadSchema, v);
  }

  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/review`, { cache: 'no-store' });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    return null;
  }

  const json = (await res.json()) as unknown;
  return validateOrThrow(ReviewPayloadSchema, json);
}

export async function saveReview(jobId: string, payload: ReviewPayload): Promise<void> {
  if (isMockMode()) {
    mockStorageSet(`review:${jobId}`, payload);
    return;
  }

  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/review`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    return;
  }

  // Optional backend persistence: keep a client-side PoC fallback.
  mockStorageSet(`review:${jobId}`, payload);
}

export function exportFinalBomJson(args: {
  job: JobDetail;
  renderId: string;
  review: ReviewPayload;
}): string {
  const render = args.job.renders.find((r) => r.id === args.renderId);
  if (!render) {
    throw new Error('render not found');
  }

  const bom = buildBomRows(render.detections, args.review);
  const payload = {
    jobId: args.job.id,
    updatedAt: args.review.updatedAt,
    renderId: render.id,
    bom,
  };

  return JSON.stringify(payload, null, 2);
}
