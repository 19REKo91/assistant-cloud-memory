# CHRONO CROSS GPT — Reader Acceptance Test Plan

Date: 2026-10-16
Status: **Prepared; not executed against the Floot app**
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
