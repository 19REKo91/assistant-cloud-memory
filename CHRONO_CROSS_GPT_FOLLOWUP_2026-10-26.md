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
- During this preview-only status check, the pairing UUID was not returned or written to this memo. A later, separately verified GitHub Actions run used the current pairing ID as its workflow input; GitHub's job log displays that input, but the MCP bearer token remained masked and was not printed.
- The preview check reported viewport 292×319 with no horizontal document overflow; this is a narrow preview viewport check, not a full visual review on the user's physical screen.

## Free-host options assessed
- **Live-session MCP round trip (completed 2026-10-26):** GitHub Actions run [40314462507](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40314462507) succeeded using the pairing ID from the currently open CHRONO Diagnostics panel. Logs verified MCP `initialize` (HTTP 200, protocol `2025-11-25`), `notifications/initialized` (202), `tools/list` (all 3 expected tools), capability query, `read_public_page` against `https://example.com/`, missing/wrong-token rejection, and URL safety validation. The `control_browser_workspace` navigation was delivered once and returned `acknowledged`; `pageLoadVerified` was explicitly `false`. The token was masked/not printed. The workflow page remains https://github.com/19REKo91/assistant-cloud-memory/actions/workflows/chrono-cross-gpt-mcp-production-handshake.yml. GitHub displays the pairing ID in the workflow input logs, so avoid posting those logs publicly.
- **Cloudflare Workers AI Playground:** official docs support remote MCP testing and describe an OAuth connection flow; the docs reviewed do not verify compatibility with CHRONO's current static Bearer-token authentication. Do not put the production token there without a clear trusted auth path. Reference: https://developers.cloudflare.com/agents/model-context-protocol/guides/test-remote-mcp-server/.
- **MCPJam Inspector:** free plan and static Bearer-token configuration are documented, and hosted mode describes server-side secure credential storage. Using it would still transfer a high-privilege production token to a third party; no secret was submitted. Reference: https://www.mcpjam.com/pricing and https://github.com/stijnhaus/mcpjam-inspector/blob/main/docs/inspector/guided-oauth.mdx.
- **Direct ChatGPT Free Android attachment:** still unavailable through the documented custom-MCP path. OpenAI's current Help Center says custom MCP connections are web-only and available to Business and Enterprise/Edu, with Pro support limited to read/fetch; this user wants free-only options. Reference: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt.

## Status
- Published diagnostics-copy correction: **COMPLETE**; verified against live assets.
- MCP endpoint configuration and authentication rejection: **PASS**.
- Disposable browser MCP → Realtime → UI → persisted ACK E2E: **PASS**.
- Current user's open preview session ID/localStorage consistency: **PASS**, without exposing its value.
- Actual live navigate+matching ACK in the user's current preview session: **PASS** in GitHub Actions run [40314462507](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40314462507); page load itself remains unverified by the MCP acknowledgement.
- Direct attachment of this ChatGPT Free Android conversation as the MCP host: **NOT SUPPORTED BY THE DOCUMENTED CUSTOM-MCP PATH**.
- Trusted free external host controlling the live session: **not yet verified**.

## Immediate next step
- The live-session command round trip is complete; do not repeat it unless the pairing ID changes or bridge code changes.
- The remaining blocker is a supported external MCP host. OpenAI's current Help Center says custom MCP connections are web-only and unavailable on mobile; Pro is limited to read/fetch, and this user is on Free Android. Therefore the current ChatGPT conversation cannot be attached as a custom MCP host through the documented route.
- Do not move the production bearer token into a third-party hosted inspector solely to make the status panel turn green. If a free hosted MCP client is chosen later, first review its credential handling and verify it supports static bearer auth; do not claim it is attached until it successfully calls this endpoint.
- Keep `hostConnection=not_verified` and `ChatGPT host connection = HOST SETUP REQUIRED` until an external host is actually connected and verified. No Floot code change can grant MCP-host capability to an unsupported ChatGPT plan/surface.


## Addendum — free push-triggered MCP command bridge (2026-10-26)

- Added `.github/workflows/chrono-cross-gpt-browser-command-bridge.yml`, `tools/chrono-cross-gpt-browser-command.mjs`, `tools/chrono-browser-command.json`, and `tools/CHRONO_GITHUB_ACTIONS_BRIDGE.md`.
- Workflow run [40316351650](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40316351650) succeeded with the initial request safely disabled. After strengthening URL query-key validation, run [40316501435](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40316501435) also succeeded and logged `status: skipped`, `reason: command_disabled`, `credentialPrinted: false`. These confirm the workflow launches and the current request remains disabled; they do **not** prove a live command through the new bridge.
- The bridge triggers only when `tools/chrono-browser-command.json` changes on `main`; it reads `CHRONO_MCP_TOKEN` and `CHRONO_BROWSER_SESSION_ID` from GitHub Actions secrets, validates the request, and requires an acknowledged MCP command. No secrets are in the repository files.
- **Public-repository warning:** the repository visibility is public. The command JSON and git history are therefore public; use only public, non-sensitive URLs. Common credential-like query parameter names are blocked, but do not include private page links or sensitive query values.
- **Required manual setup before live use:** add a repository Actions secret named `CHRONO_BROWSER_SESSION_ID` with the pairing ID from the currently open CHRONO Diagnostics panel. The existing `CHRONO_MCP_TOKEN` secret is already confirmed configured. Do not paste either value into chat or commit them.
- The initial request file is `enabled: false`. It has not executed any browser command. Once the session secret is configured, the assistant can update the request file with an explicitly requested public navigation/tab action; the push-triggered job will act as the MCP client. Its acknowledgement still does not verify page loading.
- This is a **free GitHub Actions command bridge**, not a native attachment of the current ChatGPT Free Android conversation as an MCP host. Keep the app's `HOST SETUP REQUIRED` / `hostConnection=not_verified` indicator unchanged until a supported native host handshake is available.

## Updated next action
User should add the `CHRONO_BROWSER_SESSION_ID` repository secret using GitHub Settings → Secrets and variables → Actions, while keeping CHRONO open with Realtime browser bridge connected. After the user confirms setup, run one harmless public-navigation command through the new push-triggered bridge and verify both the GitHub acknowledgement and the visible CHRONO address/state before marking the bridge live.
