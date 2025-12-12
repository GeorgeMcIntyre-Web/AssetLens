'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { buildBomRows, effectiveAccepted, effectiveAssetType, type BomRow } from '@/lib/bom';
import { exportFinalBomJson, getJobDetail, getReview, saveReview } from '@/lib/api';
import { ReviewPayloadSchema, type Detection, type JobDetail as JobDetailT, type ReviewPayload } from '@/lib/schemas';
import { emptyReview, setAccepted, setRelabelAssetType } from '@/lib/reviewState';
import { validate } from '@/lib/validate';

function badgeClass(status: JobDetailT['status']): string {
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

function readLocalReview(jobId: string): ReviewPayload | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(`review:${jobId}`);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    const v = validate(ReviewPayloadSchema, parsed);
    if (!v.ok) {
      return null;
    }
    return v.value;
  } catch {
    return null;
  }
}

function writeLocalReview(jobId: string, payload: ReviewPayload): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(`review:${jobId}`, JSON.stringify(payload));
}

function downloadText(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
}

function DetectionsList(props: {
  detections: Detection[];
  review: ReviewPayload;
  selectedDetectionId: string | null;
  selectedAssetType: string | null;
  onSelectDetection: (id: string) => void;
  onToggleAccepted: (id: string, accepted: boolean) => void;
  onRelabel: (id: string, assetType: string | null) => void;
}) {
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {props.detections.map((d) => {
        const accepted = effectiveAccepted(d, props.review);
        const assetType = effectiveAssetType(d, props.review);
        const isSelected = props.selectedDetectionId === d.id;
        const isAssetSelected = props.selectedAssetType ? assetType === props.selectedAssetType : false;

        const bg = isSelected
          ? 'rgba(124, 92, 255, 0.22)'
          : isAssetSelected
            ? 'rgba(34, 197, 94, 0.12)'
            : 'rgba(255,255,255,0.03)';

        return (
          <div
            key={d.id}
            className="panel"
            style={{ padding: 10, background: bg, cursor: 'pointer' }}
            onClick={() => props.onSelectDetection(d.id)}
          >
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div style={{ fontWeight: 700 }}>{assetType}</div>
              <div className="small">{Math.round(d.confidence * 100)}%</div>
            </div>
            <div className="row" style={{ marginTop: 8 }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  props.onToggleAccepted(d.id, !accepted);
                }}
                className={accepted ? 'primary' : ''}
              >
                {accepted ? 'Accepted' : 'Rejected'}
              </button>
              <input
                placeholder="Relabel assetType…"
                value={assetType}
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => {
                  const v = e.target.value;
                  props.onRelabel(d.id, v.length > 0 ? v : null);
                }}
                style={{
                  flex: 1,
                  minWidth: 140,
                  padding: '8px 10px',
                  borderRadius: 10,
                  border: '1px solid var(--border)',
                  background: 'rgba(255,255,255,0.04)',
                  color: 'var(--text)',
                }}
              />
            </div>
            <div className="small" style={{ marginTop: 6 }}>
              id: {d.id}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BomTable(props: {
  rows: BomRow[];
  selectedAssetType: string | null;
  onSelectAssetType: (assetType: string | null) => void;
}) {
  if (props.rows.length === 0) {
    return <div className="empty">No accepted detections yet.</div>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>assetType</th>
          <th>count</th>
        </tr>
      </thead>
      <tbody>
        {props.rows.map((r) => {
          const selected = props.selectedAssetType === r.assetType;
          return (
            <tr
              key={r.assetType}
              style={{ background: selected ? 'rgba(34, 197, 94, 0.12)' : 'transparent', cursor: 'pointer' }}
              onClick={() => props.onSelectAssetType(selected ? null : r.assetType)}
            >
              <td style={{ fontWeight: 700 }}>{r.assetType}</td>
              <td>{r.count}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ImageViewer(props: {
  imageUrl: string;
  renderWidth: number;
  renderHeight: number;
  detections: Detection[];
  review: ReviewPayload;
  selectedDetectionId: string | null;
  selectedAssetType: string | null;
  onSelectDetection: (id: string) => void;
}) {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [rect, setRect] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    function update() {
      const el = imgRef.current;
      if (!el) {
        return;
      }
      const r = el.getBoundingClientRect();
      setRect({ w: r.width, h: r.height });
    }

    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, [props.imageUrl]);

  const scaleX = rect ? rect.w / props.renderWidth : 1;
  const scaleY = rect ? rect.h / props.renderHeight : 1;

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        ref={imgRef}
        src={props.imageUrl}
        alt="render"
        style={{ width: '100%', height: 'auto', display: 'block', borderRadius: 12, border: '1px solid var(--border)' }}
        onLoad={() => {
          const el = imgRef.current;
          if (!el) {
            return;
          }
          const r = el.getBoundingClientRect();
          setRect({ w: r.width, h: r.height });
        }}
      />

      {rect
        ? props.detections.map((d) => {
            const assetType = effectiveAssetType(d, props.review);
            const accepted = effectiveAccepted(d, props.review);

            if (!accepted) {
              return null;
            }

            const isSelected = props.selectedDetectionId === d.id;
            const isAssetSelected = props.selectedAssetType ? assetType === props.selectedAssetType : false;

            const [x, y, w, h] = d.bbox;
            const left = x * scaleX;
            const top = y * scaleY;
            const width = w * scaleX;
            const height = h * scaleY;

            const border = isSelected
              ? '2px solid rgba(124, 92, 255, 0.95)'
              : isAssetSelected
                ? '2px solid rgba(34, 197, 94, 0.85)'
                : '1px solid rgba(230, 234, 242, 0.55)';

            const bg = isSelected ? 'rgba(124, 92, 255, 0.10)' : 'rgba(0,0,0,0)';

            return (
              <div
                key={d.id}
                onClick={() => props.onSelectDetection(d.id)}
                title={`${assetType} (${Math.round(d.confidence * 100)}%)`}
                style={{
                  position: 'absolute',
                  left,
                  top,
                  width,
                  height,
                  border,
                  background: bg,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
              />
            );
          })
        : null}
    </div>
  );
}

export default function JobDetail({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<JobDetailT | null>(null);
  const [review, setReview] = useState<ReviewPayload>(() => emptyReview(jobId));
  const [selectedRenderId, setSelectedRenderId] = useState<string | null>(null);
  const [selectedDetectionId, setSelectedDetectionId] = useState<string | null>(null);
  const [selectedAssetType, setSelectedAssetType] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setError(null);
      try {
        const [j, r] = await Promise.all([getJobDetail(jobId), getReview(jobId)]);
        if (cancelled) {
          return;
        }

        setJob(j);

        const local = readLocalReview(jobId);
        const initial = r ?? local;
        if (initial) {
          setReview(initial);
        } else {
          setReview(emptyReview(jobId));
        }

        const first = j.renders.at(0)?.id ?? null;
        setSelectedRenderId(first);
      } catch (e) {
        if (cancelled) {
          return;
        }
        setError(e instanceof Error ? e.message : 'failed to load job');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  useEffect(() => {
    // Optional backend persistence; always keep a client-only fallback.
    writeLocalReview(jobId, review);

    const t = window.setTimeout(() => {
      void saveReview(jobId, review);
    }, 350);

    return () => window.clearTimeout(t);
  }, [jobId, review]);

  const render = useMemo(() => {
    if (!job) {
      return null;
    }

    const targetId = selectedRenderId ?? job.renders.at(0)?.id;
    if (!targetId) {
      return null;
    }

    return job.renders.find((r) => r.id === targetId) ?? null;
  }, [job, selectedRenderId]);

  const detections = useMemo(() => render?.detections ?? [], [render]);

  const bomRows = useMemo(() => buildBomRows(detections, review), [detections, review]);

  if (error) {
    return (
      <div className="panel">
        <div style={{ fontSize: 18, fontWeight: 700 }}>Job detail</div>
        <div className="empty" style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Could not load job</div>
          <div className="small">{error}</div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="panel">
        <div className="empty">Loading…</div>
      </div>
    );
  }

  if (!render) {
    return (
      <div className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Job {job.id}</div>
            <div className="small">No renders uploaded for this job.</div>
          </div>
          <span className={badgeClass(job.status)}>{job.status}</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>Job {job.id}</div>
            <div className="small">Created: {job.createdAt}</div>
          </div>
          <span className={badgeClass(job.status)}>{job.status}</span>
        </div>
        <div style={{ height: 12 }} />
        <div className="row">
          <label className="small" style={{ width: 100 }}>
            Render
          </label>
          <select
            value={render.id}
            onChange={(e) => {
              setSelectedDetectionId(null);
              setSelectedAssetType(null);
              setSelectedRenderId(e.target.value);
            }}
            style={{
              padding: '8px 10px',
              borderRadius: 10,
              border: '1px solid var(--border)',
              background: 'rgba(255,255,255,0.04)',
              color: 'var(--text)',
            }}
          >
            {job.renders.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id}
              </option>
            ))}
          </select>
          <div className="small">{detections.length} detections</div>
        </div>
      </div>

      <div className="grid3">
        <div className="panel">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Viewer</div>
          <ImageViewer
            imageUrl={render.imagePath.startsWith('/jobs/') ? `/api${render.imagePath}` : render.imagePath}
            renderWidth={render.width}
            renderHeight={render.height}
            detections={detections}
            review={review}
            selectedDetectionId={selectedDetectionId}
            selectedAssetType={selectedAssetType}
            onSelectDetection={(id) => setSelectedDetectionId(id)}
          />
          <div className="small" style={{ marginTop: 10 }}>
            Tip: click a BOM row to highlight detections of that assetType.
          </div>
        </div>

        <div className="panel">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Detections</div>
          <DetectionsList
            detections={detections}
            review={review}
            selectedDetectionId={selectedDetectionId}
            selectedAssetType={selectedAssetType}
            onSelectDetection={(id) => setSelectedDetectionId(id)}
            onToggleAccepted={(id, accepted) => setReview((prev) => setAccepted(prev, id, accepted))}
            onRelabel={(id, assetType) => setReview((prev) => setRelabelAssetType(prev, id, assetType))}
          />
        </div>

        <div className="panel">
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontWeight: 700 }}>BOM</div>
            <button
              onClick={() => {
                const json = exportFinalBomJson({ job, renderId: render.id, review });
                downloadText(`${job.id}-bom.json`, json);
              }}
            >
              Export BOM JSON
            </button>
          </div>
          <BomTable rows={bomRows} selectedAssetType={selectedAssetType} onSelectAssetType={setSelectedAssetType} />
          <div style={{ height: 10 }} />
          <div className="small">Only accepted detections are counted.</div>
        </div>
      </div>
    </div>
  );
}
