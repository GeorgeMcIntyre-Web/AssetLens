import type { Detection, ReviewPayload } from '@/lib/schemas';
import { getReviewInstance } from '@/lib/reviewState';

export type BomRow = { assetType: string; count: number };

export function effectiveAssetType(d: Detection, review: ReviewPayload): string {
  const i = getReviewInstance(review, d.id);
  const override = i?.relabelAssetType;
  if (override && override.length > 0) {
    return override;
  }

  return d.assetType;
}

export function effectiveAccepted(d: Detection, review: ReviewPayload): boolean {
  const i = getReviewInstance(review, d.id);
  if (!i) {
    return true;
  }

  if (typeof i.accepted === 'boolean') {
    return i.accepted;
  }

  return true;
}

export function buildBomRows(detections: Detection[], review: ReviewPayload): BomRow[] {
  const counts = new Map<string, number>();

  for (const d of detections) {
    if (!effectiveAccepted(d, review)) {
      continue;
    }

    const key = effectiveAssetType(d, review);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const rows = Array.from(counts.entries()).map(([assetType, count]) => ({ assetType, count }));

  rows.sort((a, b) => {
    if (b.count !== a.count) {
      return b.count - a.count;
    }
    return a.assetType.localeCompare(b.assetType);
  });

  return rows;
}
