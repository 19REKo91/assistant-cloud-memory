# CHRONO CROSS GPT — follow-up 2026-10-26

## Scope and safety
- Project: `d5d93380-474a-4949-b0f8-5d2b05cce845`.
- Production URL: https://chrono-cross-gpt.floot.app.
- Floot confirms the app is published on the **free** plan (`paid=false`); no paid feature or native build was used.
- No value of `CHRONO_MCP_TOKEN` was read, printed, copied, or added to this memo.
- The only production code change in this continuation is a diagnostics-copy clarification; no authentication, token, database, or browser-control logic was changed.

## Source change and publish
- Project source version before the diagnostics edit: `1792659934587`.
- In `pages/_index.tsx`, replaced the obsolete `STALE · RUN #19 · 2026-10-20` label with `E2E PASS · RUN #40172582749 · ISOLATED SESSION`.
- Updated nearby explanatory text to state that this successful E2E used an isolated browser session and does not prove a ChatGPT host is attached.
- Left `ChatGPT host connection = HOST SETUP REQUIRED` because no direct ChatGPT-host handshake is verified.
- Project source version after edits: `1793011992486`.
- Floot checkpoint: `91173f3f-8a62-4d2d-b910-44ac5ee2f03e` (Clarified MCP E2E status and host limitation).
- Following the user's authorization to edit, published the diagnostics-copy change to the existing production subdomain. Publish job `cb6d99fd-49b6-4db6-b44b-b9eb14f62f47` completed with status `succeeded`; production URL remained unchanged.
- No production environment or domain setting was modified.

## Tests and production verification
- Floot default suite: **9 spec files passed, 0 failed**.
- Explicit hook specs `helpers/useDebounce.spec.tsx` and `helpers/useMediaQuery.spec.tsx`: **2 passed, 0 failed**.
- Total distinct spec files run: **11 passed, 0 failed**.
- Project TypeScript typecheck: **clean**.
- Post-publish HTTP verification:
  - `GET /_api/mcp-status`: HTTP 200, `tokenConfigured=true`, `hostConnection=not_verified`.
  - MCP `initialize` without Authorization: HTTP 401.
  - MCP `initialize` with a deliberately invalid test Bearer: HTTP 401.
  - Fetch of live page and script assets: HTTP 200; checked deployed assets and confirmed the updated E2E label and the correct `HOST SETUP REQUIRED` label are both present.
  - No request returned or logged the configured token.
- GitHub Actions run [40172582749](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40172582749) is confirmed completed successfully; job `live-control-e2e` succeeded across all listed steps. It verifies a disposable Playwright/Chromium session, not the owner's live preview.

## Current preview/session check
- The supported Floot preview runner returned safe status only: Diagnostics visible, updated E2E label present, `HOST SETUP REQUIRED` present, localStorage available, and the displayed pairing ID matched the browser's current localStorage value.
- The pairing UUID was not returned, written to this memo, or sent in a command.
- The preview check reported viewport 292×319 with no horizontal document overflow; this is a narrow preview viewport check, not a full visual review on the user's physical screen.

## Free-host options assessed
- **Preferred next test: existing GitHub Actions manual workflow.** The current workflow `.github/workflows/chrono-cross-gpt-mcp-production-handshake.yml` already accepts an optional `browser_session_id` workflow input. It keeps `CHRONO_MCP_TOKEN` in the existing GitHub Actions secret and the smoke-test script sends the real `control_browser_workspace` navigate command then requires a persisted matching ACK. Its output does not intentionally print the session ID or token. Workflow page: https://github.com/19REKo91/assistant-cloud-memory/actions/workflows/chrono-cross-gpt-mcp-production-handshake.yml.
- **Cloudflare Workers AI Playground:** official docs support remote MCP testing and describe an OAuth connection flow; the docs reviewed do not verify compatibility with CHRONO's current static Bearer-token authentication. Do not put the production token there without a clear trusted auth path. Reference: https://developers.cloudflare.com/agents/model-context-protocol/guides/test-remote-mcp-server/.
- **MCPJam Inspector:** free plan and static Bearer-token configuration are documented, and hosted mode describes server-side secure credential storage. Using it would still transfer a high-privilege production token to a third party; no secret was submitted. Reference: https://www.mcpjam.com/pricing and https://github.com/stijnhaus/mcpjam-inspector/blob/main/docs/inspector/guided-oauth.mdx.
- **Direct ChatGPT Free Android attachment:** still unavailable through the documented custom-MCP path. OpenAI's current Help Center says custom MCP connections are web-only and available to Business and Enterprise/Edu, with Pro support limited to read/fetch; this user wants free-only options. Reference: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt.

## Status
- Published diagnostics-copy correction: **COMPLETE**; verified against live assets.
- MCP endpoint configuration and authentication rejection: **PASS**.
- Disposable browser MCP → Realtime → UI → persisted ACK E2E: **PASS**.
- Current user's open preview session ID/localStorage consistency: **PASS**, without exposing its value.
- Actual live navigate+matching ACK in the user's current preview session: **NOT YET RUN**.
- Direct attachment of this ChatGPT Free Android conversation as the MCP host: **NOT SUPPORTED BY THE DOCUMENTED CUSTOM-MCP PATH**.
- Trusted free external host controlling the live session: **not yet verified**.

## Immediate next step
The connected GitHub toolset can inspect Actions runs but does not expose a workflow-dispatch action. To prove the personal-session round trip without moving the token to a new provider, open the workflow page above, select **Run workflow**, copy the current pairing ID from the open CHRONO Diagnostics panel into the optional `browser_session_id` field, and run it while the CHRONO tab remains open. The workflow should report a browser-control `acknowledged` result if the user's live tab receives the command and stores the matching ACK. Do not mark this complete until that run succeeds. Do not print the token, do not share the pairing ID in a public issue or source file, and do not change `hostConnection` unless a real host handshake is verified.
