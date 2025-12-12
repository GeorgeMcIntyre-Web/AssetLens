import { describe, expect, it } from 'vitest';

import type { Detection } from '@/lib/schemas';
import { buildBomRows } from '@/lib/bom';
import { emptyReview, setAccepted, setRelabelAssetType } from '@/lib/reviewState';

describe('BOM grouping/sorting', () => {
  it('groups accepted detections by effective assetType and sorts', () => {
    const detections: Detection[] = [
      { id: 'd1', assetType: 'widget', confidence: 0.9, bbox: [0, 0, 10, 10] },
      { id: 'd2', assetType: 'widget', confidence: 0.9, bbox: [0, 0, 10, 10] },
      { id: 'd3', assetType: 'gizmo', confidence: 0.9, bbox: [0, 0, 10, 10] },
      { id: 'd4', assetType: 'alpha', confidence: 0.9, bbox: [0, 0, 10, 10] },
    ];

    let review = emptyReview('j1');

    // relabel one widget to gizmo
    review = setRelabelAssetType(review, 'd2', 'gizmo');

    // reject alpha
    review = setAccepted(review, 'd4', false);

    const rows = buildBomRows(detections, review);

    expect(rows).toEqual([
      { assetType: 'gizmo', count: 2 },
      { assetType: 'widget', count: 1 },
    ]);
  });

  it('sorts by count desc then assetType asc', () => {
    const detections: Detection[] = [
      { id: 'd1', assetType: 'b', confidence: 0.9, bbox: [0, 0, 10, 10] },
      { id: 'd2', assetType: 'a', confidence: 0.9, bbox: [0, 0, 10, 10] },
    ];

    const review = emptyReview('j1');
    const rows = buildBomRows(detections, review);
    expect(rows).toEqual([
      { assetType: 'a', count: 1 },
      { assetType: 'b', count: 1 },
    ]);
  });
});
