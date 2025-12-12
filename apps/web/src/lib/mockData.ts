import jobsJson from '../../../../sample-data/expected/jobs.json';
import jobMock1 from '../../../../sample-data/expected/job_mock_1.json';

import { JobDetailSchema, JobsListSchema, type JobDetail, type JobSummary } from '@/lib/schemas';
import { validateOrThrow } from '@/lib/validate';

export function expectedJobs(): JobSummary[] {
  return validateOrThrow(JobsListSchema, jobsJson);
}

export function expectedJobDetail(jobId: string): JobDetail {
  const byId: Record<string, unknown> = {
    job_mock_1: jobMock1,
  };

  const raw = byId[jobId];
  if (!raw) {
    throw new Error(`mock job not found: ${jobId}`);
  }

  return validateOrThrow(JobDetailSchema, raw);
}
