export { SCHEMA_VERSION } from './schemas/constants';

export {
  CommitHashSchema,
  JobIdSchema,
  ProvenanceSchema,
  Sha256Schema,
  TraceIdSchema
} from './schemas/common';
export type { Provenance } from './schemas/common';

export { JobInputSchema, JobManifestSchema, JobOptionsSchema } from './schemas/jobManifest';
export type { JobManifest } from './schemas/jobManifest';

export { DetectionSchema, DetectionsDocumentSchema } from './schemas/detection';
export type { Detection, DetectionsDocument } from './schemas/detection';

export { BomComponentSchema, BomDocumentSchema, ComponentHashSchema } from './schemas/bom';
export type { BomComponent, BomDocument } from './schemas/bom';
