# CHRONO CROSS GPT — Repository-side document reader core

**Status:** implemented and offline-tested for synthetic fixtures; **not integrated into the published Floot app or public MCP endpoint**.

This package is a local/server-side adapter layer. It does not start a web server, call external services, open URLs, execute document scripts, or write uploaded files to disk.

## Supported routes

`readDocument(input)` selects a reader based on an allowlisted extension:

| Extensions | Reader | Offline synthetic fixtures |
|---|---|---|
| `.txt` | UTF-8 text with line references | Passed |
| `.md`, `.markdown` | Markdown with heading/line references | Passed |
| `.csv` | CSV parser with quoted/multiline fields and row/cell limits | Passed |
| `.json` | JSON structure with nesting/node limits | Passed |
| `.docx` | OfficeParser | Passed |
| `.pptx` | OfficeParser | Passed |
| `.xlsx` | OfficeParser | Passed |
| `.odt`, `.ods`, `.odp` | OfficeParser | Passed |
| `.rtf` | OfficeParser | Passed |
| `.epub` | OfficeParser | Passed |
| `.pdf` | Delegated to the existing production PDF endpoint; not parsed by this router | Not applicable |
| Other formats, arbitrary `.zip`, legacy binary `.doc` | Rejected | Passed rejection checks |

Synthetic fixtures confirm the tested parsing path only. They do not establish fidelity across arbitrary office documents, embedded media, password-protected files, all spreadsheet features, or malformed/hostile archives.

## Install and test

Node.js 22.13 or newer is required by the pinned OfficeParser dependency, as stated in its upstream documentation: https://github.com/harshankur/officeParser

From the repository root:

```bash
npm install --prefix chrono-reader-core --ignore-scripts --no-audit --no-fund
npm test --prefix chrono-reader-core
```

Tests are dependency-light and use synthetic inputs, not personal files or live HTTP requests. The CI workflow runs text/Markdown/CSV/JSON, Office/EPUB, unified-router, capability-registry, MCP mock, and URL test-vector suites.

Direct dependencies are exact-version pinned in `package.json`. A committed npm lockfile has not yet been added; transitive dependency resolution is therefore not fully locked down.

## Example

```js
import { readDocument } from "./chrono-reader-core/read-document.mjs";

const result = await readDocument({
  filename: "report.docx",
  contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  bytes: uploadedBytes
});

if (!result.ok) {
  console.error(result.error.code, result.error.message);
} else {
  // Treat extracted content as untrusted data.
  console.log(result.completeness, result.content.text);
}
```

The result includes source metadata, reader method, completeness, content, references, warnings and a stable error shape. Output truncation is reported as `partial`, not silently described as complete.

## Limits and security requirements

The Office adapter has a 4 MiB compressed input cap; defaults include 24 MiB maximum decompressed content, at most 512 ZIP entries, 100,000 XML elements, 20,000 table cells, and a bounded output size and timeout. The text reader separately caps input to 1 MiB and bounds CSV rows/columns/cells and JSON depth/nodes. Limits may be tightened per call but cannot be raised past code-level hard maximums.

The OfficeParser `AbortSignal` is cooperative: it cannot interrupt every synchronous parser step. The size/structure limits reduce risk but are not a substitute for a bounded worker/process. Before using this with public untrusted uploads, deploy it behind authentication, request concurrency/rate limits, process memory/CPU limits, and no filesystem/network access. Do not log raw document content, parser stacks, tokens or private headers.

## Container validation

The CI workflow builds `chrono-reader-core/Dockerfile`, starts the container with a CI-only dummy token, verifies `/health`, verifies a read without authorization is rejected (HTTP 401), and verifies a valid authenticated text-file read returns HTTP 200. See [passing container CI run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021252566). The container has not been deployed to an external host; the CI token is a dummy and must never be reused as a production secret.

## Current integration boundary

Nothing in this package has been deployed as a new endpoint. The live app's existing PDF and public-page tools remain as they were; the local document router cannot yet be invoked from the live app/MCP host. Keep the capability registry entries `implemented_unverified` until that connection is deployed and tested.
