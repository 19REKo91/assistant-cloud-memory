# CHRONO CROSS GPT — Reader Acceptance Test Plan

Date: 2026-10-17
Status: **Plan update complete; repository tests and selected production smoke tests recorded; full Floot/product acceptance remains incomplete**
Branch: `chronocross-offline-prep-2026-10-16`

## Purpose

Define repeatable, evidence-based acceptance tests for the reading capabilities requested for CHRONO CROSS GPT. This plan is independent of Floot's daily build quota. It does not claim that any reader is implemented or passing merely because a test is specified.

## Status vocabulary

- **Implemented and tested** — observed passing on the named build/runtime with reproducible evidence.
- **Implemented, unverified** — code appears to exist but a valid runtime test has not confirmed it.
- **Planned** — testable requirement with no confirmed implementation.
- **Blocked/unavailable** — depends on an unavailable runtime, provider, permission, or quota.
- **Partial** — a supported subset works; limitations are stated.

## Test fixture policy

Use small, non-sensitive public fixtures and synthetic files. Never use private user documents, secrets, or login credentials in test fixtures. Record fixture URL or checksum, test date, build/deployment identifier, observed result, and relevant error without logging tokens.

## Acceptance matrix

| ID | Capability | Fixture / action | Pass criteria | Expected failure handling |
|---|---|---|---|---|
| WEB-01 | Public HTML article | Read a stable public article | Title, source URL, readable text, headings where available | Clear retrieval/extraction error; no invented content |
| WEB-02 | Metadata | Article with title, description, canonical URL, language/date metadata | Return only metadata actually present | Missing metadata is null/omitted, not guessed |
| WEB-03 | Alternate extraction | Use a public page that defeats the primary extractor | Approved fallback is attempted and method is identified | If all fail, report partial/failed extraction |
| WEB-04 | Redirects | Safe URL redirecting to another public URL | Final URL is reported; redirect policy enforced | Reject unsafe destination/protocol or redirect loop |
| WEB-05 | SSRF protections | localhost, private IP, link-local, unsupported schemes, encoded host tricks | Requests are rejected before access to private/internal targets | Safe typed error; no internal response leakage |
| WEB-06 | Resource limits | Oversized response, slow response, excessive redirects | Time, size, and redirect limits are enforced | Timeout/size-limit status; no hang |
| WEB-07 | Untrusted page content | Page contains prompt-injection text | Text is treated as source data, not executable instructions | No tool invocation or policy change caused by page text |
| PDF-01 | Selectable-text PDF | Small multi-page PDF with headings | Text and page boundaries preserved sufficiently for reading | Report pages with missing/empty text |
| PDF-02 | Scanned PDF | Image-only PDF | Detect low/no selectable text and report OCR required or invoke tested OCR | Do not present empty extraction as complete |
| PDF-03 | Malformed/encrypted PDF | Invalid or password-protected fixture | Specific unsupported/encrypted error | No crash or secret prompt |
| DOC-01 | DOCX | Synthetic document with headings, lists, and tables | Text order, headings, table content retained | Unsupported content is reported |
| OFFICE-01 | PPTX | Synthetic slides with title and bullet text | Slide boundaries and order retained | Embedded media limitations stated |
| SHEET-01 | XLSX/CSV | Multiple sheets, headers, blank cells, numeric and date values | Sheet names, headers, rows, and table structure retained | Unsupported formula/image details stated; no silent flattening |
| TXT-01 | Markdown/plain text | Unicode and Arabic RTL fixture | Unicode intact; headings/lists preserved where applicable | Invalid encoding reported explicitly |
| OCR-01 | Screenshot/image | Clear image containing Arabic and Latin text | Extracted text labeled as OCR; uncertain characters flagged when possible | Low-confidence/illegible regions acknowledged |
| VIS-01 | Chart/diagram | Image with labeled axes, legend, and values | Describe only visible evidence; preserve labels and uncertainty | Do not invent data from unreadable pixels |
| AUDIO-01 | Audio transcription | Short permitted audio fixture | Transcript returned with method and language; timestamps if supported | State provider/configuration blocker clearly |
| VIDEO-01 | Video captions | Public video with available captions | Caption text and timestamps retrieved with source attribution | Explain unavailable captions or access restrictions |
| VIDEO-02 | Video without captions | Small permitted test video | If integrated, audio transcription/frame path is identified separately | Do not claim translation/dubbing without tested provider |
| BOOK-01 | Long-form document | Multi-chapter EPUB or equivalent supported fixture | TOC/chapter boundaries and bounded chunking retained | Unsupported format/size is clear |
| CODE-01 | Repository/source | Public source file with line references | Path and line references preserved; code is not executed merely by reading | Fetch failure/permission boundary reported |
| MULTI-01 | Multi-page research | A bounded set of public pages linked from a seed | Source URLs/citations retained; duplicates controlled; crawl limit enforced | Stop at limits and report partial coverage |
| LANG-01 | Arabic and mixed RTL/LTR | Arabic paragraph with URLs, numbers, and code | Text is not corrupted or reordered in stored result | Report encoding/layout limitations |
| AUTH-01 | Private/login-gated page | Synthetic inaccessible/private URL | No access without explicit supported authorization | Never bypass login, paywall, CAPTCHA, or access control |
| API-01 | Capability reporting | Query the capability registry | Each capability reports accurate status, method, limits, dependencies | No planned/blocked capability presented as available |
| API-02 | Error contract | Trigger timeout, unsupported type, empty result, invalid input | Stable typed error and actionable message | No stack trace, secret, or internal data leakage |

## Test execution record template

For every run, record:

- Test ID:
- Date/time (UTC):
- App URL/build/version:
- Runtime/provider and version:
- Fixture URL or non-sensitive checksum:
- Expected result:
- Actual result:
- Status: PASS / FAIL / BLOCKED / NOT RUN
- Evidence (redacted logs or screenshot reference):
- Defect and next action:

## Minimum release gate

Do not mark a capability as **implemented and tested** until its happy path and relevant failure cases pass. For public web reading, the minimum release gate is WEB-01 through WEB-07 plus LANG-01 and API-01. Security cases must fail closed. A test that cannot run because Floot quota is exhausted is **BLOCKED**, not PASS.

## First execution sequence when Floot is available

1. Re-read current production/source state; record exact build/deployment.
2. Run WEB-01, WEB-02, WEB-04, WEB-05, WEB-06, WEB-07, and LANG-01.
3. Run PDF-01 and PDF-02 only after confirming supported PDF dependency/runtime.
4. Capture sanitized results and update the project notebook.
5. Fix one failure class at a time; rerun the relevant regression tests.


## Executed production evidence — 2026-10-17

The following rows have production evidence from the automated reader smoke test; all other rows in the matrix remain plans unless separately linked to a passing run.

| ID | Observed status | Evidence | Exact scope / remaining limitation |
|---|---|---|---|
| WEB-01 (narrow smoke subset) | **Partial pass** | [MCP reader smoke run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019598377) | `read_public_page` returned HTTP 200 and contained the expected `Example Domain` marker for one stable public URL. This is not representative coverage for arbitrary websites. |
| WEB-05 (scheme-rejection subset only) | **Partial pass** | [MCP reader smoke run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019598377) | `file:///etc/passwd` was rejected as a tool error without making a filesystem/network probe. Private DNS answers, redirect-to-private targets, DNS rebinding, and complete canonicalization defense remain unproven. |
| PDF-01 (two-page selectable text subset) | **Pass for synthetic fixture** | [Two-page PDF production run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019833832) | A synthetic two-page PDF was uploaded to production; both unique per-page text markers appeared in the result (HTTP 200). This checks extraction across both pages, but does not yet verify the result's page-by-page structured boundaries or real-world layout/tables. |
| PDF-02 | **Not implemented / not tested** | No evidence | Image-only/scanned PDF detection and OCR remain unavailable. |
| PDF-03 (narrow rejection subset) | **Pass for tested fixtures** | [Two-page PDF production run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019833832) | One malformed synthetic PDF returned HTTP 422; one plain-text upload to the PDF endpoint returned HTTP 415. Encrypted PDFs and other malformed/archive edge cases remain untested. |

All production tests use non-sensitive synthetic/public fixtures, avoid printing response content, and never send credentials to arbitrary destinations. Production fixture success must not be treated as full security certification or end-to-end feature completeness.


## Repository-side text-document reader tests — 2026-10-17

Offline CI run [39020214789](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39020214789) passed the new bounded UTF-8/Markdown/CSV/JSON adapter regression suite. Coverage includes:

- Plain text preserves Arabic Unicode and line references; filenames are reduced to a safe basename.
- Markdown headings are indexed with source line numbers while original text is retained.
- CSV parsing handles quoted commas, escaped quotes, CRLF, multiline quoted values and inconsistent-width rows; malformed quoting and configured row/column/cell overages fail safely.
- JSON parses into structured data, rejects malformed input, and enforces nesting/node-count bounds.
- Empty input, invalid UTF-8, NUL-containing bytes, input size limits, oversized typed-array input, unsupported extensions, and MIME mismatches return stable failures without echoing submitted content.

Boundary: these results apply to the repository module `chrono-reader-core/read-text-document.mjs` only. It is not connected to the published Floot app or an external API, so the UI/MCP cannot invoke this reader yet. The capability registry intentionally labels it `implemented_unverified`, not production-tested.


## Office adapters and unified routing — offline evidence, 2026-10-17

CI run [39020767305](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39020767305) completed **success** with the following repository-side tests:

- Synthetic **DOCX** and **PPTX** inputs each returned the expected unique text marker.
- Synthetic **XLSX** returned the worksheet header, a string cell and a numeric cell.
- Synthetic **RTF** returned the expected text.
- The unified router selected the UTF-8 text reader for Arabic text, the CSV reader for tabular data and the Office adapter for DOCX. It deliberately reports PDF as delegated to the existing production PDF endpoint; it does not pretend PDF is parsed by this local adapter.
- Rejected inputs included malformed ZIP/Office data, MIME/extension mismatch, legacy `.doc`, arbitrary `.zip`, empty files, oversized input and unsupported types. Output clipping is labelled as a partial result.
- The Office adapter uses pinned `officeparser@8.1.1` and `fflate@0.8.2`, with explicit file-size, decompression, ZIP-entry, XML-element, cell, repeated-content, output-size and timeout caps.

**Important boundary:** all these checks are deterministic offline synthetic fixtures. They prove that the repository modules work for the tested fixtures, not that the uploaded files can yet be submitted to CHRONO CROSS GPT through its published UI or MCP service. The registry keeps the new reader/router entries `implemented_unverified` until a real integration is deployed and tested. All eight allowlisted Office/ebook formats (DOCX, PPTX, XLSX, ODT, ODS, ODP, RTF and EPUB) now have synthetic fixtures that passed offline CI run [39020912180](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39020912180). This verifies only those synthetic paths; OCR, image understanding, audio/video transcription and rendered-page browser automation remain unimplemented here.


## Authenticated reader bridge container — 2026-10-17

CI run [39021252566](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021252566) passed both loopback HTTP contract tests and a Docker end-to-end smoke test. The image built successfully; the container served its health endpoint, rejected an unauthenticated POST with HTTP 401, and returned HTTP 200 with the expected text from an authenticated synthetic text-file upload. The test token is a CI-only dummy, never a deployment credential.

This validates the server/container contract only. The container has **not** been deployed to an external host, does not yet receive uploaded files from the published Floot UI, and is not connected as an additional MCP tool. A production secret must be configured via the hosting platform's secret manager. Keep `bridge.reader_api` at `implemented_unverified` until a deployment and secured integration are tested.


## Consolidated acceptance status — 2026-10-17

This section supersedes the initial header's date and compiles the execution evidence gathered after the original plan was drafted. **Completing this plan document is not the same as accepting the whole product.** Rows marked "offline" prove only the tested repository fixtures; only the rows explicitly marked "production" were exercised against the current live Floot deployment.

| Acceptance ID | Current result | Evidence | Acceptance boundary / what remains |
|---|---|---|---|
| MCP-01 | **PASS — production handshake** | [Production MCP handshake run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019598377) | Authenticated protocol handshake and tool-list/tool calls were exercised in that run. This does not establish a direct ChatGPT Android app attachment or persistent host session. |
| WEB-01 | **PASS — one public fixture only** | [Production reader smoke](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019343189) | Public-page tool returned expected Example Domain text. Arbitrary-site extraction quality remains unverified. |
| WEB-05 | **PARTIAL — one scheme rejection** | [Production MCP smoke](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019224577) | The `file:` scheme was rejected without probing a private resource. Private DNS answers, redirect-to-private destinations, DNS rebinding and every canonicalization edge remain unproven. |
| PDF-01 | **PASS — synthetic two-page PDF** | [Production PDF smoke](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019833832) | Both unique page text markers appeared in the HTTP 200 extraction response. Structured page-by-page boundaries, tables, real-world layout and larger documents remain unverified. |
| PDF-02 | **NOT IMPLEMENTED** | No production evidence | Scanned/image-only PDF OCR has no integrated, tested path. |
| PDF-03 | **PASS — limited validation fixtures** | [Production PDF smoke](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39019833832) | One malformed PDF was rejected with HTTP 422; one text upload with HTTP 415. Encrypted PDFs and broader malformed/polyglot files remain untested. |
| FILES-01 | **PASS — synthetic text formats, offline** | [Current aggregate CI](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021709319) | UTF-8 text (including Arabic), Markdown headings, CSV quoting/multiline/limits, JSON nesting/node limits, invalid encoding, size limits, and MIME/extension rejection pass. This router is not wired to the public product. |
| OFFICE-01 | **PASS — eight synthetic formats, offline** | [Eight-format Office/ebook tests](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39020912180) | DOCX, PPTX, XLSX, ODT, ODS, ODP, RTF and EPUB synthetic fixtures return expected text. Real documents, complex workbook formulas/formatting, embedded media, encryption and high-fidelity table/slide/page boundaries remain unverified. |
| ROUTER-01 | **PASS — offline** | [Router CI](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021709319) | Dispatches text/CSV/Office fixtures; explicitly delegates PDF to the existing production endpoint. The router is not used by live Floot/MCP yet. |
| BRIDGE-01 | **PASS — 13 loopback HTTP cases, offline** | [Bridge plus container CI](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021252566) | Auth required, invalid tokens/JSON/Base64 rejected, fields restricted, size/response/concurrency limits tested, stable errors returned, and credentials not echoed. Loopback only, not public hosting. |
| BRIDGE-02 | **PASS — Docker container smoke, offline** | [Container run](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021636008) | Container build and health check passed; unauthenticated POST returned HTTP 401; authenticated synthetic file read returned HTTP 200. Test used a dummy-only token and platform-style `PORT=10000`. It does not prove an external service is deployed. |
| HOST-01 | **PASS — Blueprint policy check only** | [Render Blueprint CI](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021709319) | Render declaration remains Free, manual-deploy only, correct Docker context/health path, and requires a dashboard-entered secret. It has **not** been applied; no Render instance or production token exists. |
| INTEGRATION-01 | **NOT ACCEPTED / NOT DEPLOYED** | [Integration handoff](https://github.com/19REKo91/assistant-cloud-memory/blob/chronocross-offline-prep-2026-10-16/docs/CHRONO_CROSS_READER_BRIDGE_INTEGRATION.md) | The new readers and bridge are repository-side only. Floot has no verified server-side proxy call to this bridge and MCP does not expose the file reader. |
| WORKSPACE-01 | **UNVERIFIED** | No passing live evidence | Local persistence changes in Floot are incomplete/unpublished; restore/persist UI wiring and the relevant Floot typecheck/tests remain unverified. |
| OCR / IMAGE / AUDIO / VIDEO | **NOT ACCEPTED** | No passing evidence | OCR, image understanding, audio/video transcription and video-caption retrieval are not integrated and tested as product features. |
| BROWSER-01 | **BLOCKED / NOT ACCEPTED** | No deployed runtime evidence | JavaScript-rendered browser runtime and remote DOM interaction are not available in the published deployment. |

### Final completion checklist for this plan update

- [x] Update the plan date/status.
- [x] Link successful production tests separately from offline synthetic suites.
- [x] Add text/Markdown/CSV/JSON regression suite and scope.
- [x] Add all eight Office/ebook fixture formats and scope.
- [x] Add unified-router result and explicit PDF delegation.
- [x] Add authenticated bridge API tests and Docker/health/authenticated read.
- [x] Add manual-only free Render Blueprint policy checks.
- [x] Preserve explicit limitations for SSRF/DNS rebinding, OCR, browser runtime, persistence and live integration.
- [ ] Deploy the bridge to an authorized host and verify a real HTTPS request with a newly provisioned secret.
- [ ] Wire the bridge to a server-only Floot proxy/MCP tool, run Floot typecheck/full tests, publish, and verify end-to-end.
- [ ] Finish the remaining product capabilities above before declaring the project complete.

**Plan status:** the requested documentation update is complete in this revision. **Product acceptance status: INCOMPLETE.** Do not change the overall project to "complete" until the unchecked product-level items are genuinely tested.
