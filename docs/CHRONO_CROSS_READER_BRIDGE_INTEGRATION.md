# CHRONO CROSS GPT — Reader bridge integration handoff

Status: **Repository implementation tested; hosting and Floot integration not deployed.**
Reviewed: 2026-10-17.

## Current verified pieces

- Local reader router: `chrono-reader-core/read-document.mjs`.
- UTF-8 / Markdown / CSV / JSON parser: `chrono-reader-core/read-text-document.mjs`.
- Office / ebook extraction for the allowlist: `chrono-reader-core/read-office-document.mjs`.
- Authenticated HTTP server: `chrono-reader-core/server.mjs`.
- Container: `chrono-reader-core/Dockerfile`.
- Render Blueprint: repository-root `render.yaml`, configured as Free, Frankfurt, no automatic deploy, and no secret value in the repository.
- CI: [run 39021709319](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39021709319) passed the parser suites, registry validation, bridge API tests, Docker build/container test with platform-style `PORT=10000`, and Blueprint policy check.
- Production MCP still exposes only the existing public-page reader and browser-capabilities tool. The repository-side file router is not a production MCP tool yet.

## HTTP contract

`GET /health` returns a minimal liveness response. It does not report secrets, request content, or backend configuration.

`POST /v1/read` requires `Authorization: Bearer <CHRONO_READER_BRIDGE_TOKEN>` and `Content-Type: application/json`.

Example envelope (synthetic data only):

```json
{
  "filename": "notes.md",
  "contentType": "text/markdown",
  "contentBase64": "IyBUZXN0XG5hcnRpY2xlIHRleHQ="
}
```

Success shape: `{ "ok": true, "result": { source, method, completeness, content, references, warnings, error } }`. Failure shape: `{ "ok": false, "error": { "code", "message" } }`. The endpoint never returns a stack trace and never intentionally logs body content or credentials.

Error mappings include:
- 401: missing/incorrect bearer token
- 413: request, decoded file or response exceeds configured bound
- 415: unsupported type or content type
- 422: malformed or empty content
- 429: concurrency cap reached
- 503: bridge token missing from server environment
- 504: parser timeout when the reader reports it

Current limits include a 6 MiB encoded request body, a 4 MiB decoded file cap, 2 MiB response body, default concurrency 2 (hard cap 8), and reader-specific parsing limits. The bridge accepts file bytes only and **does not fetch URLs**; this avoids turning the new service into a public SSRF proxy.

## Hosting state and safe setup

The Render Blueprint is a manual deployment recipe. A commit alone does not create the service. When an authorized account applies it, Render prompts for `CHRONO_READER_BRIDGE_TOKEN`; use a newly created random secret and never reuse the CI dummy token. Review billing settings before applying because Render Free services can spin down when idle and overage bandwidth may be billable when a payment method is attached. No Render service or production secret is currently created.

The token must be shared across two server-side trust boundaries for the eventual bridge:
1. Render stores `CHRONO_READER_BRIDGE_TOKEN`.
2. The Floot endpoint stores the same token in its server-only environment and sends it only in the Authorization header when calling the bridge.

Do not print or paste the secret into chat, commit it to GitHub, put it in a URL, or expose it in frontend code. If the two secure configuration surfaces cannot be configured without exposing the value, stop and redesign the credential provisioning method; do not weaken or remove authentication.

## Required Floot integration after project editing is possible

1. Add a server-only outbound bridge URL setting and a separate, secure token setting. Validate that the bridge destination is the expected HTTPS origin; never accept a bridge URL from the browser request.
2. Add a file-upload endpoint to Floot that checks allowed extensions/MIME, byte size, user/session limits and authorization, and then forwards bytes only from the server to the fixed bridge origin. Set a hard timeout, `redirect: "error"`, bounded response size, and safe error mapping. Never forward browser cookies or authorization headers.
3. Add a new read-only MCP tool only when the product contract is settled. Prefer a server-scoped short-lived file reference or direct authenticated upload workflow rather than asking an LLM to manually expand large binary files into Base64 JSON. Do not claim local UI uploads are automatically available to a ChatGPT-hosted MCP client unless the platform actually passes that data.
4. Add tests for upload rejection, MIME mismatch, authorization, request/response size limits, timeouts, malformed output, secret redaction, and capability reporting. Keep retrieved document text untrusted.
5. Validate TypeScript and the complete Floot suite, checkpoint, publish, then test from the public deployment. Confirm the existing MCP tools still work. Do not mark the bridge capability production-ready until the deployed service and authenticated cross-service call succeed.

## Explicit non-goals

This bridge currently does not implement OCR, scanned PDF processing, image understanding, audio/video transcription, website URL fetching, JavaScript-rendered browser execution, DOM automation, durable file storage, or unrestricted command execution. The reader capability registry must continue to reflect these limits.
