import { describe, expect, it } from 'vitest';

import { emptyReview, getReviewInstance, setAccepted, setRelabelAssetType } from '@/lib/reviewState';

describe('relabel/accept state update logic', () => {
  it('adds/updates acceptance per detection', () => {
    let review = emptyReview('j1');

    review = setAccepted(review, 'd1', false);
    expect(getReviewInstance(review, 'd1')).toEqual({ detectionId: 'd1', accepted: false });

    review = setAccepted(review, 'd1', true);
    expect(getReviewInstance(review, 'd1')).toEqual({ detectionId: 'd1', accepted: true });
  });

  it('adds/updates relabel per detection', () => {
    let review = emptyReview('j1');

    review = setRelabelAssetType(review, 'd1', 'widget');
    expect(getReviewInstance(review, 'd1')).toEqual({ detectionId: 'd1', relabelAssetType: 'widget' });

    review = setRelabelAssetType(review, 'd1', 'gizmo');
    expect(getReviewInstance(review, 'd1')).toEqual({ detectionId: 'd1', relabelAssetType: 'gizmo' });
  });

  it('removes instance when both accepted and relabel are unset', () => {
    let review = emptyReview('j1');

    review = setAccepted(review, 'd1', false);
    review = setRelabelAssetType(review, 'd1', 'widget');
    expect(getReviewInstance(review, 'd1')).toBeTruthy();

    review = setRelabelAssetType(review, 'd1', null);
    expect(getReviewInstance(review, 'd1')).toEqual({ detectionId: 'd1', accepted: false });

    // clearing accepted removes the instance
    review = setAccepted(review, 'd1', null);
    expect(getReviewInstance(review, 'd1')).toBeUndefined();
  });
});
