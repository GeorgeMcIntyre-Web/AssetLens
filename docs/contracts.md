## Contracts overview (shared schemas)

All contracts in `packages/shared` use **Zod as the single source of truth**.

### Global invariants (non-negotiables)

- **`schemaVersion`** is present on every top-level contract payload.
- **`traceId`** is present on every top-level contract payload and must be propagated across derived artifacts.
- **`provenance`** is required on every top-level contract payload:
  - `pipelineName`, `pipelineVersion`
  - `modelName`, `modelVersion`
  - `configHash` (sha256 hex)
  - `commitHash` (git sha, or `UNKNOWN` placeholder)
- **Determinism-friendly fields**:
  - `configHash` is always required.
  - `seed` is supported (optional) in `provenance` and/or per-job options.

### Versioning rules

- `schemaVersion` is **semver** (`MAJOR.MINOR.PATCH`).
- **MAJOR**: breaking changes (remove/rename fields, change types/constraints).
- **MINOR**: backward-compatible additions (new optional fields, new enum values if applicable).
- **PATCH**: clarifications/metadata only (no behavior change to validation).

### Schemas

- **Job manifest** (`JobManifestSchema`)
  - Purpose: describes an analysis job input + provenance.
  - Required: `schemaVersion`, `traceId`, `jobId`, `createdAt`, `provenance`, `input`.

- **Detections document** (`DetectionsDocumentSchema`)
  - Purpose: detector/model outputs for a job.
  - Required: `schemaVersion`, `traceId`, `jobId`, `createdAt`, `provenance`, `detections[]`.

- **BOM document** (`BomDocumentSchema`)
  - Purpose: components inventory for a job.
  - Required: `schemaVersion`, `traceId`, `jobId`, `createdAt`, `provenance`, `components[]`.

### JSON Schema export

Generate JSON Schema directly from the Zod schemas:

- `npm -w packages/shared run generate:json-schema`

This writes files to `packages/shared/json-schema/*.schema.json`.
