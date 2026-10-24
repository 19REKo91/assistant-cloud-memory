# CHRONO CROSS GPT — Live Browser-Control Verification Memo
Date: 2026-10-24 (UTC)
Repository: `19REKo91/assistant-cloud-memory`
Branch: `main`

## Verified progress
- Production MCP handshake passed before live-control testing: [run 40081031329](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081031329).
- The production tool list includes `read_public_page`, `get_browser_capabilities`, and `control_browser_workspace`.
- The offline test workflow passed after updating its workflow-dispatch validator to accept the optional `browser_session_id` input: [run 40081052217](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081052217).
- Added optional `browser_session_id` input to `.github/workflows/chrono-cross-gpt-mcp-production-handshake.yml`.
- Added conditional live navigation verification to `tools/chrono-cross-gpt-mcp-smoke-test.mjs`. When a session UUID is provided, it calls `control_browser_workspace` with `navigate https://example.com/` and requires `acknowledgementStatus=acknowledged`; otherwise it explicitly reports the control test as skipped.
- Updated the offline workflow validator to check the new optional input.

## Live-control attempt — NOT PASSED
- Run: [40081091436](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081091436)
- The command call returned HTTP 200 at the JSON-RPC transport layer, but its tool result was an error: `acknowledgementStatus=timeout`, `acknowledged=false`, `deliveryCount=1`.
- This is important evidence: the realtime layer reported one delivery, but the workspace did not return a verified acknowledgement within the endpoint timeout. Do **not** describe this as successful browser control.
- The workflow failed intentionally because the new test correctly requires an acknowledgement.
- A temporary one-run session fallback was removed immediately afterward in commit `80c9b8816931736db144800f3c6c9495d9c8425d`; no hard-coded browser session remains in the workflow.

## Commits made in this work
- `416f0ba431a9902965748696f2fa338c08d5b663` — optional workflow input for browser session UUID.
- `a1601ef13cc62cb21ba03f852310228880e61606` — live control call + acknowledgement assertion in smoke test.
- `4825c1968a8de2ce602101e467bb2686c5bfca76` — update offline workflow validation for the optional input.
- `ff87a79587a9365ab654a1a3b58ae57fa1da10ef` — temporary one-run test invocation; must not be used as final configuration.
- `80c9b8816931736db144800f3c6c9495d9c8425d` — removed temporary session fallback.

## Remaining blockers / next steps
1. **PASS after cleanup:** post-revert production handshake [run 40081125388](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081125388) and offline suite [run 40081125432](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081125432) both succeeded on commit `80c9b8816931736db144800f3c6c9495d9c8425d`. The temporary session fallback is absent; this successful handshake was protocol-only.
2. Inspect the live app's browser-control session generation, realtime subscription lifecycle, and acknowledgement endpoint. The failed live test needs a root-cause investigation; do not blindly retry commands.
3. Verify the actual workspace UUID and that the published app has the current listener/ACK implementation. Delivery count 1 alone is not proof the UI callback executed.
4. Once the bridge is fixed, rerun with the UUID supplied through the workflow input and require an explicit acknowledgement.
5. Direct connection from the user's current ChatGPT Android conversation to this MCP server remains **not configured/verified**; MCP endpoint availability does not automatically attach it to this chat.
6. Back/Forward remains intentionally deferred per the user's instruction.

## Current status
- MCP protocol/authentication/public-page reader: **COMPLETE / PASS**.
- Browser-control tool listing: **COMPLETE / PASS**.
- Live browser command/acknowledgement round trip: **INCOMPLETE / FAIL (ack timeout; delivery count 1)**.
- Direct ChatGPT host integration: **INCOMPLETE / NOT VERIFIED**.
- No credentials were written into this memo.


## Regression-test follow-up — 2026-10-24 (UTC)

- Commit `9eff4f4c031633dfcc4eb9137bb35c75f882c643` moved `CHRONO_BROWSER_SESSION_ID` UUID validation before the first MCP request, so malformed session IDs are rejected without contacting production. Protocol-only production handshake passed: [run 40081430891](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081430891). The offline workflow also passed on that commit: [run 40081430862](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081430862).
- Commit `ef6a0497642c61b9733b10870ef6a7bd8f027611` added offline mock cases for acknowledged navigation, acknowledgement timeout, explicit rejection, and invalid session IDs. Its first test run failed only because the timeout assertion over-escaped the expected JSON text: [run 40081454193](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081454193).
- Fixed that assertion in commit `6e29ced9b8c1742c956d395c098d1e153e10eb1d`. The subsequent complete offline workflow passed: [run 40081486428](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081486428). The run validated workflow/config files and script syntax, then passed the mocked success, SSE, auth, response-ID, server-identity, missing-tool, ACK, timeout, rejection, invalid-session-ID, and missing/malformed-token cases.
- These are **mocked regression tests plus a protocol-only live handshake**. They do not change the status of the real browser-control round trip. The last real live command test remains failed with `acknowledgementStatus=timeout`, `acknowledged=false`, and `deliveryCount=1`.
- A fresh Floot tool refusal at 2026-10-24 09:17 UTC confirmed its daily build-action limit is still exhausted, with reset at `2026-10-25T07:00:00Z`. Floot source files and runtime diagnostics could not be inspected in this session; no Floot app code was changed or republished.
- Next action after the Floot limit resets: inspect the current published-source parity, active realtime subscription/channel and event payload in `pages/_index.tsx`, command state transitions in `endpoints/mcp_POST.ts`, and ACK validation/response in `endpoints/browser-control-ack_POST.ts`; then make a targeted fix and verify one real command/ACK round trip. Do not mark complete before the live acknowledgement succeeds.
