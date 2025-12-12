import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { zodToJsonSchema } from 'zod-to-json-schema';

import {
  BomDocumentSchema,
  DetectionsDocumentSchema,
  JobManifestSchema
} from '../src/index';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const outDir = path.join(__dirname, '..', 'json-schema');

const schemas = [
  { name: 'jobManifest', schema: JobManifestSchema },
  { name: 'detections', schema: DetectionsDocumentSchema },
  { name: 'bom', schema: BomDocumentSchema }
];

await mkdir(outDir, { recursive: true });

for (const entry of schemas) {
  if (typeof entry.name !== 'string') {
    throw new Error('Missing schema name');
  }

  if (entry.name.length === 0) {
    throw new Error('Missing schema name');
  }

  if (entry.schema === undefined) {
    throw new Error(`Missing Zod schema for ${entry.name}`);
  }

  if (entry.schema === null) {
    throw new Error(`Missing Zod schema for ${entry.name}`);
  }

  const jsonSchema = zodToJsonSchema(entry.schema, {
    name: entry.name,
    $refStrategy: 'none'
  });

  const outPath = path.join(outDir, `${entry.name}.schema.json`);
  await writeFile(outPath, `${JSON.stringify(jsonSchema, null, 2)}\n`, 'utf8');
}
