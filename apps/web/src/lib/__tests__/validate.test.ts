import { describe, expect, it } from 'vitest';

import { JobsListSchema } from '@/lib/schemas';
import { validate, validateOrThrow } from '@/lib/validate';

describe('validate utilities', () => {
  it('validate() returns ok=true for valid payload', () => {
    const input = [{ id: 'j1', status: 'created', createdAt: '2025-12-12T00:00:00Z' }];
    const res = validate(JobsListSchema, input);
    expect(res.ok).toBe(true);
    if (!res.ok) {
      throw new Error('expected ok');
    }
    expect(res.value[0]?.id).toBe('j1');
  });

  it('validate() returns ok=false for invalid payload', () => {
    const input = [{ id: '', status: 'nope', createdAt: 123 }];
    const res = validate(JobsListSchema, input);
    expect(res.ok).toBe(false);
    if (res.ok) {
      throw new Error('expected error');
    }
    expect(res.error.length).toBeGreaterThan(0);
  });

  it('validateOrThrow() throws for invalid payload', () => {
    expect(() => validateOrThrow(JobsListSchema, { nope: true })).toThrow();
  });
});
