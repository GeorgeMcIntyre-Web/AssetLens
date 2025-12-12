'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';

import { createJob, runPipeline } from '@/lib/api';
import type { JobSummary } from '@/lib/schemas';

export default function CreateJob() {
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [renderFiles, setRenderFiles] = useState<File[]>([]);
  const [result, setResult] = useState<JobSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => Boolean(jobFile) && !busy, [jobFile, busy]);

  async function onSubmit() {
    setError(null);
    setResult(null);

    if (!jobFile) {
      setError('Please choose a job.json file.');
      return;
    }

    setBusy(true);
    try {
      const created = await createJob({ jobFile, renderFiles });
      setResult(created);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'failed to create job');
    } finally {
      setBusy(false);
    }
  }

  async function onRun() {
    if (!result) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const updated = await runPipeline(result.id);
      setResult(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'failed to run');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div className="panel" style={{ background: 'rgba(255,255,255,0.03)' }}>
        <div className="row">
          <label style={{ width: 140, color: 'var(--muted)' }}>job.json</label>
          <input
            type="file"
            accept="application/json,.json"
            onChange={(e) => setJobFile(e.target.files?.item(0) ?? null)}
          />
        </div>
        <div style={{ height: 10 }} />
        <div className="row">
          <label style={{ width: 140, color: 'var(--muted)' }}>renders</label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => setRenderFiles(Array.from(e.target.files ?? []))}
          />
        </div>
        <div style={{ height: 12 }} />
        <div className="row">
          <button className="primary" onClick={onSubmit} disabled={!canSubmit}>
            {busy ? 'Working…' : 'Create job'}
          </button>
          <div className="small">{jobFile ? jobFile.name : 'No file selected'}</div>
        </div>
      </div>

      {error ? (
        <div className="empty">
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Error</div>
          <div className="small">{error}</div>
        </div>
      ) : null}

      {result ? (
        <div className="panel" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700 }}>Job created</div>
              <div className="small">ID: {result.id}</div>
            </div>
            <span className="badge">{result.status}</span>
          </div>
          <div style={{ height: 12 }} />
          <div className="row">
            <button onClick={onRun} disabled={busy} className="primary">
              Run pipeline
            </button>
            <Link href={`/jobs/${encodeURIComponent(result.id)}`}>
              <button>Open job</button>
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
