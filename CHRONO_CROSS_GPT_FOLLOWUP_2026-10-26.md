# CHRONO CROSS GPT — follow-up 2026-10-26

## Scope and safety
- Project: `d5d93380-474a-4949-b0f8-5d2b05cce845`.
- Production URL remains https://chrono-cross-gpt.floot.app.
- Floot status read during this session: published=true, plan=free, paid=false.
- No publish, unpublish, production configuration change, or secret read was performed.
- No value of `CHRONO_MCP_TOKEN` was printed, copied, or added to this memo.

## Confirmed baseline
- Latest documented production MCP-to-workspace browser-control E2E: GitHub Actions run [40172582749](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40172582749), successful on 2026-10-25, using a disposable Playwright/Chromium context.
- That run verifies the MCP → Realtime → CHRONO workspace UI → persisted acknowledgement flow for the disposable test session only. It does not verify the owner's current browser session or this ChatGPT conversation.
- The live `/ _api/mcp-status` status from the prior verified probe was HTTP 200, `tokenConfigured=true`, `hostConnection=not_verified`; unauthenticated MCP initialize was rejected with HTTP 401. Do not change this state absent a real host handshake.
- ChatGPT Free on Android has no documented direct custom-MCP attachment path. Do not recommend paid features; direct ChatGPT connection remains incomplete.

## Source change made in Floot preview
- Floot project source version before edit: `1792659934587`.
- Updated `pages/_index.tsx` to replace the obsolete Diagnostics label `STALE · RUN #19 · 2026-10-20` with `E2E PASS · RUN #40172582749 · ISOLATED SESSION`.
- Updated the MCP endpoint panel copy to explain that this E2E passed in an isolated browser session and does not prove ChatGPT or another persistent host is connected.
- Kept `ChatGPT host connection = HOST SETUP REQUIRED` intentionally; no verified host connection exists.
- Floot source version after edit: `1793011992486`.
- A Floot checkpoint was created: `91173f3f-8a62-4d2d-b910-44ac5ee2f03e` (`Clarified MCP E2E status and host limitation`).
- The edit is in the Floot project/preview source only. **It has not been published**; production remains unchanged.

## Verification after the edit
- Ran `helpers/mcpEndpoint.spec.tsx`, `helpers/mcpStatusEndpoint.spec.tsx`, and `helpers/browserControlAck.spec.tsx`: **3 spec files passed, 0 failed**.
- Floot type diagnostics for `pages/_index.tsx`: **clean**.
- `CHRONO_MCP_TOKEN` value remains undisclosed. The status endpoint's boolean is not proof that an external host is connected.

## Current status
- Production MCP endpoint/authentication: PASS per the last verified production probe.
- Disposable-browser E2E and matching ACK: PASS in run 40172582749.
- Targeted regression tests after UI-copy change: PASS (3/3).
- Diagnostics stale-label correction: implemented in Floot source, not yet published.
- Direct ChatGPT Free Android attachment: INCOMPLETE / no documented supported path.
- Persistent browser session controlled by an alternative free MCP host: INCOMPLETE / not tested.

## Next safe step
1. Inspect the updated Floot preview and confirm the Diagnostics copy is legible on mobile.
2. Continue testing a trusted free MCP client only if it supports the required Bearer header without exposing the production token to an untrusted hosted service.
3. Do not publish this UI-copy-only correction unless the owner explicitly wants it live; do not mark ChatGPT host connected until an actual host handshake and matching live command acknowledgement are observed.
