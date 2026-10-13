# CHRONO CROSS GPT — Assistant Notebook

Last updated: 2026-10-13 (UTC)

## Purpose
This is the durable working notebook for the assistant to resume the CHRONO CROSS GPT project without asking King to repeat earlier context. Update this file after meaningful work sessions.

## Current status
- Project: **CHRONO CROSS GPT**, a browser/assistant-side web tool built in Floot.
- Floot project ID: `d5d93380-474a-4949-b0f8-5d2b05cce845`.
- A browser-like interface and public-page text reader were created.
- MCP HTTP endpoint files were added:
  - `endpoints/mcp_POST.ts`
  - `endpoints/mcp_POST.schema.ts`
- MCP methods implemented include `initialize`, `ping`, `tools/list`, `tools/call`, `resources/list`, and `prompts/list`.
- Tools exposed by the endpoint: `read_public_page({url})` and `get_browser_capabilities({})`.
- The page reader uses Jina Reader for public pages and includes URL restrictions, request limits/timeouts, and a warning that retrieved page content is untrusted.
- A setup note exists at `static/chrono-mcp-setup.md`.
- Tests include `helpers/mcpEndpoint.spec.tsx`, `helpers/readPageEndpoint.spec.tsx`, and `helpers/themeMode.spec.tsx`.
- The last known successful validation before the credential step was a clean typecheck and 3 passing spec files.
- Last known checkpoint: `eb59a02d-e20e-4614-9c96-a6f58aa39caf`, titled “MCP endpoint hardened and tested”.
- Headless browser dependencies were rejected by Floot; do not claim the app has full automated Chromium/DOM browsing. The current reader is not equivalent to a full browser automation engine.
- The app has **not been published publicly**. Do not publish without King’s explicit permission.

## Credential status
- On 2026-10-13, Floot confirmed the secure credential flow succeeded for the generic credential named **CHRONO CROSS GPT MCP Access Token**.
- Secret environment variable available to the project: `CHRONO_MCP_TOKEN`.
- Floot reported the stored value has 34 characters. The secret itself was not revealed to the assistant and must never be requested in chat, logged, or written to this notebook/repository.
- The endpoint is intended to return HTTP 503 until `CHRONO_MCP_TOKEN` is configured; now that the credential is connected, verify the endpoint actually reads and checks the env var.

## Current blocker
- On 2026-10-13 at about 08:33 UTC, Floot refused further build actions because the Free plan’s daily build-action limit had been reached.
- Floot reported the limit resets at **2026-10-14 07:00 UTC** (10:00 AM Asia/Baghdad).
- This is a platform quota restriction, not a code failure. Status polling and preview/status checks may still be available.

## Next steps after the limit resets
1. Re-open the Floot project and inspect the current contents of `endpoints/mcp_POST.ts`, `endpoints/mcp_POST.schema.ts`, and `helpers/mcpEndpoint.spec.tsx`.
2. Verify the handler reads `process.env.CHRONO_MCP_TOKEN`, compares the Authorization Bearer token safely, and never logs the secret. Check missing-token and wrong-token paths return a safe unauthorized/unavailable response; verify valid-token requests can reach the MCP handler.
3. Run typecheck and the MCP endpoint tests. Fix any failures, then run the broader test suite if quota permits.
4. Test the endpoint through the Floot project/server context without printing or exposing the token. Never place the token in a URL, public configuration, source code, or GitHub.
5. Update this notebook with the actual test results, errors, changed files, and the next action.
6. Do not publish the app or claim it is connected to ChatGPT as an MCP client unless that has been separately configured and verified.

## Working rules
- Keep this notebook current after each meaningful session.
- Record what was completed, what remains, the verified state, and the next step.
- Distinguish verified facts from assumptions; do not claim a test passed unless its result confirms it.
- Never store credentials or secret values here.
- Do not publish publicly without King’s explicit permission.
