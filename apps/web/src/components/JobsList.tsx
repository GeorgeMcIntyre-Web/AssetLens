'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import { listJobs } from '@/lib/api';
import type { JobSummary } from '@/lib/schemas';

function statusBadgeClass(status: JobSummary['status']): string {
  if (status === 'completed') {
    return 'badge ok';
  }
  if (status === 'failed') {
    return 'badge bad';
  }
  if (status === 'running') {
    return 'badge warn';
  }
  return 'badge';
}

export default function JobsList() {
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const items = await listJobs();
        if (cancelled) {
          return;
        }
        setJobs(items);
      } catch (e) {
        if (cancelled) {
          return;
        }
        setError(e instanceof Error ? e.message : 'failed to load');
        setJobs([]);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const rows = useMemo(() => jobs ?? [], [jobs]);

  if (jobs === null) {
    return <div className="empty">Loading…</div>;
  }

  if (error) {
    return (
      <div className="empty">
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Could not load jobs</div>
        <div className="small">{error}</div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="empty">
        <div style={{ fontWeight: 700, marginBottom: 6 }}>No jobs yet</div>
        <div className="small">Create a job to start a review session.</div>
      </div>
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Status</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((j) => (
          <tr key={j.id}>
            <td>
              <Link href={`/jobs/${encodeURIComponent(j.id)}`}>{j.id}</Link>
            </td>
            <td>
              <span className={statusBadgeClass(j.status)}>{j.status}</span>
            </td>
            <td className="small">{j.createdAt}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
