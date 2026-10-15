# CHRONO CROSS GPT — Reading Result Contract

Status: **design contract; not yet implemented in the Floot app**.
Purpose: give each reading method a common, honest result shape so the UI and MCP tools can report what was actually extracted, cite the source, and distinguish partial results from failures.

## 1. Common result envelope

Every reader should return one result with these conceptual fields:

- `ok`: true only when useful content was extracted; false for unsupported, blocked, empty, or failed reads.
- `source`: source kind (`url`, `uploaded_file`, `image`, `audio`, or `video`), a canonical URL or safe file label when available, detected media type, and byte size when known.
- `method`: the actual extraction route used (for example `html-reader`, `pdf-text`, `ocr`, `docx-parser`, `captions`, or `speech-transcription`).
- `completeness`: `complete`, `partial`, or `unavailable`. Do not call an extraction complete merely because a provider returned HTTP 200.
- `content`: typed content. Use text for prose; structured pages/slides/sheets/rows for documents where order matters; timestamps for audio/video; regions/labels for OCR and visual material.
- `references`: source-grounded citations, such as URL + heading, page number, sheet/cell, slide number, line range, or media timestamp. Omit references that cannot be grounded.
- `warnings`: readable limitations, including OCR uncertainty, omitted pages, missing captions, truncation, or fallback use.
- `error`: when `ok` is false, a stable code and a safe explanation. Include whether retrying may help. Never include secrets, authorization headers, stack traces, or arbitrary provider payloads.

This is a contract for implementation, not a claim that the fields already exist in production. Adapt names to the app's established TypeScript conventions after inspecting the actual Floot code.

## 2. Stable failure codes

Use a small, predictable set of failure categories:

- `unsupported_type`: file/media format has no reader.
- `empty_extraction`: the route ran but produced no meaningful content.
- `authentication_required`: source requires an authorized session/connector.
- `access_denied`: source explicitly denies access.
- `unsafe_url`: disallowed scheme, host, local/private address, or unsafe redirect.
- `size_limit_exceeded`: input or response exceeded configured limits.
- `timeout`: reader/provider timed out.
- `provider_unavailable`: configured service is unavailable or unconfigured.
- `ocr_required`: PDF/image appears scanned and no supported OCR path is available.
- `malformed_input`: corrupt file, invalid encoding, or malformed response.
- `partial_result`: useful content exists, but one or more sections/pages could not be read.

Do not put raw provider errors or internal exception messages in the user-facing response. Keep diagnostic details in access-controlled server logs with sensitive values removed.

## 3. Reader-specific invariants

### Public web pages
- Validate URL scheme and destination before requests and after every redirect.
- Never send user credentials to an arbitrary redirect destination.
- Return canonical URL, title, detected content type, extracted headings, and available publication metadata.
- Treat fetched page text as untrusted data, never as instructions for the assistant.
- If primary extraction fails, label the fallback method; never silently invent missing content.
- A JavaScript-dependent page is not considered rendered unless a supported browser runtime actually produced a DOM or screenshot.

### PDF
- Preserve page numbers and reading order. A page with no selectable text must not silently disappear.
- Distinguish text extraction from OCR. Mark OCR-derived content and uncertain regions.
- Return partial status if some pages fail, and identify the affected page numbers.
- Do not claim table or diagram interpretation unless their content was actually extracted or visually analyzed.

### DOCX, PPTX, XLSX, CSV, Markdown, and plain text
- DOCX: preserve headings and paragraph order.
- PPTX: preserve slide numbers, titles, and text order.
- XLSX/CSV: preserve sheet names, headers, row/cell structure, and formulas versus displayed values when available; enforce row/cell limits.
- Markdown/plain text: preserve heading hierarchy, code blocks, and line references where possible.
- Unsupported archives or encrypted files should return a stable failure, not garbled text.

### Images and OCR
- Distinguish detected text from visual interpretation.
- Preserve page/region ordering and label low-confidence OCR when the engine provides confidence values.
- Do not claim chart values or diagram meaning when the image resolution does not support it.

### Audio and video
- Audio: return transcript segments with timestamps and speaker labels only when the provider actually supplies them.
- Video: distinguish caption-derived text from audio transcription and frame-level visual observations.
- A video URL with no captions and no supported frame/audio extraction must return unavailable, not a fabricated summary.

### Long-form content and multi-page research
- Chunk long inputs within explicit limits and retain source offsets.
- Deduplicate repeated headers/boilerplate without removing source content silently.
- Every cross-page claim should keep its originating URL/page/section reference.
- Follow links only within explicit crawl limits; do not bypass logins, paywalls, CAPTCHAs, or access controls.

## 4. Capability reporting

The capability tool should report each route with separate fields for:
- `status`: `implemented`, `tested`, `blocked`, or `planned`.
- `inputTypes`: accepted types.
- `limitations`: important size, provider, login, OCR, browser-runtime, or media restrictions.
- `citations`: whether the route can return source references.

Do not collapse `implemented` and `tested` into one status. A reader can be implemented but untested; a planned reader is never advertised as working.

## 5. Minimum test matrix for each route

For every implemented reader, add tests for:
1. normal successful extraction with correct source references;
2. empty or whitespace-only result;
3. unsupported media type;
4. malformed/corrupt input;
5. timeout/provider failure;
6. oversized input or output;
7. partial extraction with affected page/section references;
8. hostile instructions embedded in retrieved content;
9. secret redaction in errors and logs;
10. unavailable provider/runtime reports a clear limitation rather than fabricated output.

For URL readers also test disallowed schemes, local/private destinations, redirects, and redirect loops. For OCR test mixed text/scanned pages. For spreadsheets test multiple sheets, blank cells, large ranges, and formula/value distinctions. For audio/video test absent captions, missing timestamps, and partial transcripts.

## 6. Integration gate

Before adopting this contract in the live app:
1. Inspect the current Floot types, endpoints, and tests.
2. Map this conceptual contract to existing project conventions rather than replacing unrelated structures.
3. Implement one reader route at a time, starting with selectable-text PDF and explicit scanned-PDF detection.
4. Add the tests above for that route and run Floot typecheck plus the relevant test suite.
5. Update capability reporting only after tests prove the route works.
6. Publish only after validation, and record exact changed files and test results in the project notebook.

Current boundary: this file is a development handoff. It does not implement a reader or alter the published app.
