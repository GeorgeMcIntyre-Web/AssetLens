import { readFile } from 'node:fs/promises';

import { describe, expect, it } from 'vitest';

import {
  BomDocumentSchema,
  DetectionsDocumentSchema,
  JobManifestSchema
} from '../packages/shared/src/index';

async function readFixtureJson(fileName: string): Promise<unknown> {
  if (fileName.length === 0) {
    throw new Error('fixture filename is required');
  }

  const url = new URL(`./fixtures/${fileName}`, import.meta.url);
  const raw = await readFile(url, 'utf8');
  return JSON.parse(raw) as unknown;
}

describe('shared contract schemas', () => {
  it('sample job.json parses', async () => {
    const payload = await readFixtureJson('job.json');
    const result = JobManifestSchema.safeParse(payload);
    expect(result.success).toBe(true);
  });

  it('sample detections.json parses', async () => {
    const payload = await readFixtureJson('detections.json');
    const result = DetectionsDocumentSchema.safeParse(payload);
    expect(result.success).toBe(true);
  });

  it('sample bom.json parses', async () => {
    const payload = await readFixtureJson('bom.json');
    const result = BomDocumentSchema.safeParse(payload);
    expect(result.success).toBe(true);
  });

  it('invalid job manifest missing schemaVersion fails', async () => {
    const payload = await readFixtureJson('job.json');
    const bad = { ...(payload as Record<string, unknown>) };
    delete bad.schemaVersion;

    const result = JobManifestSchema.safeParse(bad);
    expect(result.success).toBe(false);
  });

  it('invalid detections score outside [0,1] fails', async () => {
    const payload = await readFixtureJson('detections.json');
    const doc = payload as Record<string, unknown>;
    const detections = doc.detections as Array<Record<string, unknown>>;

    if (detections.length === 0) {
      throw new Error('expected at least one detection in fixture');
    }

    const detection0 = detections[0];
    if (detection0 === undefined) {
      throw new Error('expected detection[0] in fixture');
    }

    const badDetection0 = { ...detection0, score: 2 };
    const bad = { ...doc, detections: [badDetection0] };

    const result = DetectionsDocumentSchema.safeParse(bad);
    expect(result.success).toBe(false);
  });

  it('invalid bom commitHash placeholder must be UNKNOWN or git sha', async () => {
    const payload = await readFixtureJson('bom.json');
    const doc = payload as Record<string, unknown>;
    const provenance = doc.provenance as Record<string, unknown>;

    const badProvenance = { ...provenance, commitHash: 'not-a-sha' };
    const bad = { ...doc, provenance: badProvenance };

    const result = BomDocumentSchema.safeParse(bad);
    expect(result.success).toBe(false);
  });
});
