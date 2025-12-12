import type { ReviewInstance, ReviewPayload } from '@/lib/schemas';

export function emptyReview(jobId: string): ReviewPayload {
  return { jobId, updatedAt: new Date().toISOString(), instances: [] };
}

function touch(review: ReviewPayload): ReviewPayload {
  return { ...review, updatedAt: new Date().toISOString() };
}

function normalizeInstance(i: ReviewInstance): ReviewInstance | null {
  const hasAccepted = typeof i.accepted === 'boolean';
  const relabel = i.relabelAssetType;
  const hasRelabel = typeof relabel === 'string' && relabel.length > 0;

  if (!hasAccepted && !hasRelabel) {
    return null;
  }

  const out: ReviewInstance = { detectionId: i.detectionId };

  if (hasAccepted) {
    out.accepted = i.accepted;
  }

  if (hasRelabel) {
    out.relabelAssetType = relabel;
  }

  return out;
}

export function getReviewInstance(review: ReviewPayload, detectionId: string): ReviewInstance | undefined {
  return review.instances.find((i) => i.detectionId === detectionId);
}

export function setAccepted(
  review: ReviewPayload,
  detectionId: string,
  accepted: boolean | null,
): ReviewPayload {
  const existing = getReviewInstance(review, detectionId);

  const next: ReviewInstance = {
    detectionId,
    accepted,
    relabelAssetType: existing?.relabelAssetType,
  };

  const normalized = normalizeInstance(next);
  const without = review.instances.filter((i) => i.detectionId !== detectionId);

  if (!normalized) {
    return touch({ ...review, instances: without });
  }

  return touch({ ...review, instances: [...without, normalized] });
}

export function setRelabelAssetType(
  review: ReviewPayload,
  detectionId: string,
  assetType: string | null,
): ReviewPayload {
  const existing = getReviewInstance(review, detectionId);

  const cleaned = assetType?.trim();
  const next: ReviewInstance = {
    detectionId,
    accepted: existing?.accepted ?? null,
    relabelAssetType: cleaned && cleaned.length > 0 ? cleaned : null,
  };

  const normalized = normalizeInstance(next);
  const without = review.instances.filter((i) => i.detectionId !== detectionId);

  if (!normalized) {
    return touch({ ...review, instances: without });
  }

  return touch({ ...review, instances: [...without, normalized] });
}
