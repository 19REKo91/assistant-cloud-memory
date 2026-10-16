# CHRONO CROSS GPT — External Bridge Candidate Assessment

Date: 2026-10-16
Status: **Desk research only; no hosting choice deployed or connected**
Branch: `chronocross-offline-prep-2026-10-16`

## Decision summary

Use a split model rather than trying to run every workload in one free serverless function:

1. **Cloudflare Workers Free — candidate for a lightweight authenticated routing/API bridge**, URL validation, capability metadata, and forwarding small structured requests. Do not use it as the main OCR/PDF/video-processing runtime without a concrete CPU-budget proof.
2. **Vercel Hobby — candidate for a personal-use Node.js bridge and lightweight document-processing proof of concept**, subject to request/response limits, cold starts, current terms, and package compatibility. Do not upload large files or assume that a free tier is suitable for commercial use.
3. **GitHub Actions — candidate for repository CI and reproducible tests**, not an always-on interactive API endpoint. Public repositories can use standard hosted runners free according to GitHub's billing documentation; verify current repository visibility and runner policy before relying on this.

These are candidates, not an approved deployment. No service was created, no billing was enabled, and no credentials were entered.

## Official limits checked on 2026-10-16

| Candidate | Verified published facts | Good fit | Main concern |
|---|---|---|---|
| Cloudflare Workers Free | Official docs list 100,000 requests/day, 10 ms CPU per invocation, 128 MB memory, and up to 50 subrequests per request. Request-body limits depend on the Cloudflare account plan; Free account upload limit is listed as 100 MB. | Lightweight API gateway, validation, auth, routing, short network operations | 10 ms CPU is too restrictive for heavy parsing/OCR; network calls still need strict timeout/response-size controls |
| Vercel Hobby | Official plan page describes Hobby as free and for personal projects; listed usage includes 1,000,000 function invocations and 100 GB-hours duration. Official limits pages show a 2 GB maximum memory for Hobby Node.js functions and current duration depends on Fluid Compute/configuration. | Personal-use Node.js proof of concept, moderate lightweight processing | Hobby is restricted to non-commercial personal use; function request/response body and deployment/runtime limits must be checked for the exact route |
| GitHub Actions | Official GitHub billing documentation says standard GitHub-hosted runners are free for public repositories; private repos use included minutes depending on plan, and usage beyond quota can be billed. | Automated tests, typecheck, security regression, scheduled/manual smoke tests | Not a durable always-on API; repository visibility and workflow permissions matter |

## Sources (official)

- Cloudflare Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Vercel Hobby plan: https://vercel.com/docs/plans/hobby
- Vercel general limits: https://vercel.com/docs/limits
- Vercel Functions limitations: https://vercel.com/docs/functions/limitations
- GitHub Actions billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions

## Proposed placement by workload

| Workload | Initial placement | Rationale / gate |
|---|---|---|
| Capability registry, request validation, auth/routing | Existing Floot endpoint if supported; otherwise Cloudflare Worker | Keep the bridge small, authenticated, and stateless |
| Public-page retrieval | Existing reader first; consider a narrow fallback adapter | Avoid duplicating current behavior until tested; enforce SSRF and redirect protections |
| PDF text extraction | Test existing Floot PDF.js path first; then evaluate Node.js/Vercel or a dedicated parser service | Must test package compatibility, input size, page limits, malformed/encrypted files, and memory |
| DOCX/PPTX/XLSX | Separate format-specific adapter or batch job | Preserve document structure; avoid a single giant dependency bundle |
| OCR / image understanding | External provider or separately hosted worker only after privacy/cost approval | Arabic quality, retention, file limits, latency, and actual price need testing |
| Audio/video transcription | Asynchronous job/provider path rather than synchronous edge request | Duration and payloads may exceed edge execution constraints; timestamps and rights/access rules matter |
| Automated tests | GitHub Actions | CI is appropriate; do not confuse CI with a production API |

## Security gates before a proof of concept

- Never send a bearer token from browser/frontend code if it grants broad access. Use server-side secrets and least-privilege credentials.
- Authenticate every bridge call; add rate limiting, request IDs, timeouts, and per-capability quotas.
- Validate URLs at every redirect and block loopback, private, link-local, and cloud-metadata IP ranges.
- Enforce streamed byte limits as well as declared Content-Length; cap pages, duration, output length, and concurrency.
- Redact authorization headers, tokens, and private document text from logs.
- Do not route private files through third-party providers without explicit user approval and a documented data-handling review.
- Keep OCR, video transcription, and other external processing marked unavailable until a real end-to-end test succeeds.
- Re-check official terms and limits immediately before deployment; free-tier terms and quotas can change.

## Next actions

1. Re-check Floot's current PDF upload implementation and existing dependencies when its daily build quota is available.
2. Run small local/CI compatibility tests before selecting a remote host.
3. If a remote proof of concept is still needed, begin with a tiny authenticated health/capability endpoint, not file upload or media processing.
4. Test auth failure, oversized request, malformed input, SSRF attempts, timeout, rate limit, and secret-redaction behavior.
5. Ask before deploying a new public service, granting new permissions, uploading real user data, or activating paid usage.

## Status

Research is complete for this initial shortlist, but a hosting choice is **not finalized** and no bridge is implemented. This document is not a claim that these limits guarantee suitability; verify the exact deployment configuration before use.
