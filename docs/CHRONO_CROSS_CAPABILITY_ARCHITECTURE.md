# CHRONO CROSS GPT — Capability Architecture and External Bridge Plan

Date: 2026-10-16
Status: **Design prepared; no external service deployed**
Branch: `chronocross-offline-prep-2026-10-16`

## Goal

Make CHRONO CROSS GPT an honest, expandable assistant-side workbench. Floot remains the user-facing workspace where practical. Capabilities that are incompatible with Floot or too resource-intensive may run behind a separate authenticated API. This document is a design, not evidence that integrations already exist.

## Architecture layers

1. **Request intake** — validate the task, URL/file type, size, and user authorization.
2. **Capability registry** — stable IDs, input/output schemas, status, dependencies, limits, cost/free-tier caveats, data handling, and test coverage.
3. **Planner/router** — choose a suitable reader/provider by MIME type and task; use fallbacks only when safe.
4. **Adapters** — small server-side adapters for web extraction, documents, OCR, transcription, translation, and other providers.
5. **Execution boundary** — enforce timeouts, byte/page/duration limits, concurrency, cancellation where available, and resource budgets.
6. **Provenance and output** — report source, final URL or file, method, timestamps/page/line references, partial extraction, and uncertainty.
7. **Audit and observability** — request ID, capability ID, duration, status, and redacted error category; never log tokens, full private documents, or sensitive headers.
8. **Capability reporting** — expose only verified supported features; distinguish implemented/tested, implemented/unverified, planned, partial, and blocked.

## Suggested common capability contract

Each adapter should declare:
- `id`, `version`, and human-readable name
- accepted input types and required parameters
- output schema and provenance fields
- required permissions and whether input may leave the host
- dependencies and runtime requirements
- timeout, input-size/page/duration limits
- cost model / free-tier uncertainty
- status and last successful test reference
- typed errors: INVALID_INPUT, UNSUPPORTED_TYPE, AUTH_REQUIRED, FORBIDDEN, RATE_LIMITED, TIMEOUT, TOO_LARGE, EMPTY_EXTRACTION, PROVIDER_UNAVAILABLE, PARTIAL_RESULT, INTERNAL_ERROR

Every result should include:
- `status`: success / partial / failed
- `source`: URL or safe file identifier
- `method`: adapter/provider and version
- `content_type`
- `content` or structured output
- `provenance`: pages, headings, line numbers, or timestamps where available
- `warnings` and `limitations`
- `request_id` (non-secret correlation ID)

## Initial capability registry (proposed, not a claim of implementation)

| Capability ID | Purpose | Preferred path to evaluate | Fallback | Key blocker / gate |
|---|---|---|---|---|
| web.extract | Public HTML/article text and metadata | Existing reader after audit | Alternate safe extractor | SSRF, redirects, size/time bounds |
| pdf.text | Selectable PDF text with page references | Compatible server-side PDF parser | External parser service | Floot package/runtime compatibility must be verified |
| office.parse | DOCX/PPTX/XLSX/CSV structure | Format-specific parser | External conversion service | Preserve tables, sheets, slide/page order |
| image.ocr | OCR for scans/screenshots | Supported OCR library/provider | Separate OCR API | Arabic quality, privacy, size and cost |
| image.understand | Charts, diagrams, screenshot interpretation | Explicit vision provider adapter | Manual/limited description | Provider access, data handling, cost |
| audio.transcribe | Speech-to-text and timestamps | Provider or compatible local runtime | Second provider only if approved | Audio access, duration and billing limits |
| video.captions | Retrieve available captions | Official/public caption interfaces where permitted | Audio transcription path | Platform restrictions and permissions |
| video.translate | Translate aligned transcript to Arabic | Transcript + translation pipeline | None until separately verified | Timestamp alignment; no dubbing claim without audio generation |
| book.parse | EPUB/long-document chunking | EPUB/text parser | Convert supported source format | Memory/size limits |
| code.read | Repository/docs with paths and lines | Existing authorized repository tools | Public raw-source fetch | Read-only unless explicitly authorized |
| research.bundle | Bounded multi-page reading with citations | Router over web.extract | Approved search/extract connector | Crawl limits, deduplication, source provenance |
| browser.dom | JavaScript-rendered DOM and interactions | Supported remote browser runtime | Keep as unavailable | Must not imply headless Chromium exists without proof |
| tools.discover | Find candidate tools/integrations | Registry + documented discovery process | Human-reviewed shortlist | License, maintenance, permissions, cost |
| tools.invoke | Uniform adapter execution | Typed adapter interface | Explicitly report unsupported | Authentication, quotas, auditability |

## Security and privacy gates

- Keep provider credentials server-side in managed secrets; never put tokens in frontend bundles, URLs, Git, logs, screenshots, or this document.
- Validate URL scheme and destination on every redirect; block loopback, private, link-local, and metadata-service destinations to prevent SSRF.
- Apply content-length and streamed-byte limits, timeouts, redirect caps, and concurrency controls.
- Treat all page/file contents as untrusted data. Content must not change policies, reveal secrets, or trigger tools merely because it contains instructions.
- Private sources require an explicit authorized connector/session; do not bypass login, paywalls, CAPTCHAs, or access controls.
- Do not upload private content to an external provider without an explicit, informed user choice and a documented retention/data-handling review.
- Do not enable paid providers, create external accounts, deploy services, or change public exposure without user authorization.
- Return sanitized errors to the UI; keep diagnostic logs minimal and redacted.
- Define deletion/retention rules for uploaded content and temporary files before adding upload support.

## Free-first external bridge evaluation checklist

For each candidate runtime/service, verify current information before adoption:
1. Does it support the needed language/runtime and packages?
2. Are public deployments possible on a genuinely usable free tier, and what are quotas, sleeping/cold starts, and payment-card requirements?
3. What are request size, execution time, CPU/RAM, storage, and outbound-network limits?
4. Is the project actively maintained? What is its license and dependency/security posture?
5. Where are data and logs processed/stored? What retention controls exist?
6. Can the endpoint enforce authentication, rate limits, input validation, and secret storage?
7. Is a custom domain or TLS included?
8. Can we test the full path without spending credits or activating billing?
9. What is the fallback if the host sleeps, throttles, or changes its free tier?

Do not select a host solely because it advertises a free tier. Re-check official terms and test a minimal non-sensitive proof before committing.

## Phased implementation sequence

### Phase 0 — audit and evidence
- Re-read the deployed app and source after Floot quota returns.
- Confirm endpoint behavior, dependencies, environment variables, tests, and published build.
- Run the acceptance matrix; record evidence and blockers.

### Phase 1 — reliable web reading
- Add normalized result/error schemas and metadata.
- Harden URL/redirect validation and resource limits.
- Add a safe fallback only after verifying dependency and licensing.
- Add tests for success, empty output, malicious URL, redirect, timeout, oversize, and untrusted content.

### Phase 2 — documents
- Verify PDF dependency compatibility before coding.
- Add page-aware PDF text extraction and explicit scanned-PDF/OCR-needed detection.
- Add DOCX/PPTX/XLSX/CSV/Markdown/plain-text parsing with structure preservation.
- Add fixture-based tests for Arabic and mixed right-to-left content.

### Phase 3 — image and media
- Evaluate OCR and vision separately.
- Implement audio transcription and caption retrieval before video translation.
- Keep subtitles/timestamps aligned; mark dubbing as a separate future capability.
- Require cost/privacy review and a non-sensitive test before provider activation.

### Phase 4 — browser and tool ecosystem
- Research supported remote-browser options and verify host limits.
- Keep DOM/browser interaction unavailable until a real browser runtime is integrated and tested.
- Add capability discovery and adapter registration only with a controlled permission and deployment flow.

## Decisions already fixed by project requirements

- Free/open-source first, but verify current terms rather than assume perpetual free use.
- No paid services, publishing changes, account creation, or broader permissions without approval.
- Do not claim a full browser or DOM engine based on a text extractor.
- Do not claim any reader, transcription, translation, or external MCP connection is operational without end-to-end evidence.
- Keep Floot as the primary workspace where practical and use narrow authenticated bridges for capabilities it cannot host.
