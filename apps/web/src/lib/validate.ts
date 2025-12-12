import type { ZodSchema } from 'zod';

export type ValidationOk<T> = { ok: true; value: T };
export type ValidationErr = { ok: false; error: string };
export type ValidationResult<T> = ValidationOk<T> | ValidationErr;

export function validate<T>(schema: ZodSchema<T>, input: unknown): ValidationResult<T> {
  const parsed = schema.safeParse(input);
  if (parsed.success) {
    return { ok: true, value: parsed.data };
  }

  return { ok: false, error: parsed.error.message };
}

export function validateOrThrow<T>(schema: ZodSchema<T>, input: unknown): T {
  const parsed = schema.safeParse(input);
  if (parsed.success) {
    return parsed.data;
  }

  throw new Error(parsed.error.message);
}
