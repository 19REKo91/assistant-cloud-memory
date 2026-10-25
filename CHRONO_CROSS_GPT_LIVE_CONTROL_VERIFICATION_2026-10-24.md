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

## Remaining blockers / next steps at end of 2026-10-24 (historical snapshot)
1. **PASS after cleanup:** post-revert production handshake [run 40081125388](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081125388) and offline suite [run 40081125432](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40081125432) both succeeded on commit `80c9b8816931736db144800f3c6c9495d9c8425d`. The temporary session fallback is absent; this successful handshake was protocol-only.
2. Inspect the live app's browser-control session generation, realtime subscription lifecycle, and acknowledgement endpoint. The failed live test needs a root-cause investigation; do not blindly retry commands.
3. Verify the actual workspace UUID and that the published app has the current listener/ACK implementation. Delivery count 1 alone is not proof the UI callback executed.
4. Once the bridge is fixed, rerun with the UUID supplied through the workflow input and require an explicit acknowledgement.
5. Direct connection from the user's current ChatGPT Android conversation to this MCP server remains **not configured/verified**; MCP endpoint availability does not automatically attach it to this chat.
6. Back/Forward remains intentionally deferred per the user's instruction.

## Status at end of 2026-10-24 (historical snapshot)
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


## Live E2E follow-up — 2026-10-25 (UTC)

### Floot/source inspection
- The free Floot project tools were available again. The project remains published at https://chrono-cross-gpt.floot.app on the **free** plan; no paid feature was used.
- Read the current project files before considering edits: `pages/_index.tsx`, `endpoints/mcp_POST.ts`, `endpoints/browser-control-ack_POST.ts`, `components/FlootRealtimeProvider.tsx`, `helpers/RealtimeClient.tsx`, `helpers/realtimeChannels.tsx`, `helpers/browserControl.tsx`, `helpers/browserControlAck.tsx`, the realtime token endpoint/schema, and the ACK schema.
- Project history reports the latest publish at 2026-10-24 09:08 UTC. Production `GET /_api/mcp-status` returned HTTP 200, `tokenConfigured=true`, and `hostConnection=not_verified`. That host status remains correct; this test does not attach the user's current ChatGPT conversation to MCP.
- Code inspection confirms the page and RealtimeClient use the same `getBrowserControlSessionId()` helper and channel builder. The browser handler validates command UUID/token, and the ACK endpoint atomically checks session ID, command ID, hashed one-time token, pending status, and expiry. No source-level defect was conclusively identified, so no Floot application code was changed or republished.
- The prior 2026-10-24 timeout row had `deliveryCount=1` and remained `timed_out`; production logs for that test window contained no `POST /_api/browser-control-ack`. The old pairing ID was not freshly verified against the active UI, and no Floot editor window was available during this run. Therefore the precise cause of that old timeout remains unproven; stale/mismatched session state is plausible, not confirmed.

### Added repeatable live verification
- Added `tools/chrono-cross-gpt-mcp-live-control-test.mjs` (commit `d1653a71d4be150bed1f5cfe562e282bb3dc2fef`) and `.github/workflows/chrono-cross-gpt-mcp-live-control-e2e.yml` (initial commit `78630ea88764715c47e0468b94eb0967aa2cef99`).
- The workflow opens a disposable headless Chromium instance against the published UI, reads that instance's fresh pairing UUID into process memory only, waits for the Realtime bridge to show CONNECTED, and calls the production MCP endpoint using the repository secret. Neither the UUID nor token is printed or written to repository files.
- The first workflow attempt, [run 40172550876](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40172550876), failed at MCP initialize because the initial workflow version escaped the GitHub secret expression. That workflow-only mistake was corrected in commit `bb81cd2bf8d8b1c61cf25f6397ef66b1b9306880`; the secret value was not exposed.
- The corrected live run [40172582749](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40172582749) **PASSED** on 2026-10-25. All four live checks passed:
  1. **Real navigation + ACK:** MCP returned `acknowledgementStatus=acknowledged`, delivery count 1; the UI iframe changed to the requested URL and the UI recorded “MCP acknowledgement stored”. The database row ended `acknowledged`; production logs show the ACK endpoint was called.
  2. **Explicit rejection:** selecting a nonexistent tab returned `acknowledgementStatus=rejected`; the UI recorded “MCP tab selection rejected”, the ACK endpoint was called, and the database row ended `rejected`.
  3. **Timeout path:** the test intentionally aborted the browser's ACK request after the UI received a navigation command. MCP returned `acknowledgementStatus=timeout`; the command row ended `timed_out` with delivery count 1. This is a deliberate negative test, not a failed workflow.
  4. **Invalid session:** a malformed session ID was rejected before dispatch. Only the three valid test commands were inserted into the command table.
- Independent production database readback after the run showed exactly the expected recent states: `acknowledged`, `rejected`, and `timed_out`, each with delivery count 1. Production logs showed two ACK endpoint POSTs (success and rejection); the timeout ACK was intentionally blocked by the test.
- Floot regression checks also passed: `helpers/mcpEndpoint.spec.tsx`, `helpers/browserControlAck.spec.tsx`, and `helpers/mcpStatusEndpoint.spec.tsx` all passed; targeted TypeScript typecheck was clean.

### Current status and boundaries
- MCP protocol/authentication/public-page reader: **PASS**.
- Live MCP → production Realtime → fresh production UI → trusted ACK round trip: **PASS for the disposable E2E browser session**.
- Rejection, ACK-timeout handling, and invalid-session rejection: **PASS**.
- The user's already-open personal browser session was **not tested** in this run because no Floot editor/preview window answered. Do not infer that the old pairing ID is current; if testing that exact session later, obtain the ID from its active Diagnostics panel.
- Direct ChatGPT host integration remains **NOT VERIFIED / HOST SETUP REQUIRED**; `hostConnection` remains `not_verified`. This E2E proves the MCP-to-CHRONO workspace bridge, not automatic connection to this chat.
- Back/Forward was not touched. No secrets or pairing IDs were added to public files.

## Follow-up verification — 2026-10-25 (UTC, continued)

- Re-read the current published Floot source at project version `1792659934587` before considering any code change. The project remains published at `https://chrono-cross-gpt.floot.app`; `get_publish_status` reports plan `free`, `paid=false`, and no paid feature was used.
- Re-read `pages/_index.tsx`, `endpoints/mcp_POST.ts`, `endpoints/browser-control-ack_POST.ts`, `helpers/browserControl.tsx`, `helpers/browserControlAck.tsx`, `endpoints/_realtime/token_POST.ts`, and `components/FlootRealtimeProvider.tsx`. The page and realtime channel use the same session helper/channel pattern; the token endpoint grants only `chrono-control:<sessionId>`; ACK is an atomic one-time database transition requiring matching command/session/token hash, dispatched status, and unexpired expiry.
- Re-ran targeted Floot tests: `helpers/mcpEndpoint.spec.tsx`, `helpers/browserControlAck.spec.tsx`, `helpers/mcpStatusEndpoint.spec.tsx` — **3 passed, 0 failed**. Targeted TypeScript typecheck for the UI, MCP endpoint, ACK endpoint, Realtime provider and client — **clean**.
- Attempted to inspect the user's live Floot editor DOM via the supported in-browser runner. It failed with the tool's explicit message that no open Floot tab picked up the code before timeout. This is an editor-session availability blocker, not evidence of a production defect. No pairing UUID was read, guessed, or reused.
- No Floot code change or publish was made because no root cause requiring a source change has been proven. The successful production E2E remains the disposable Chromium session from run [40172582749](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/40172582749), not the user's personal session.
- **Status remains:** production MCP → Realtime → fresh UI → ACK round trip **PASS in disposable E2E**; rejection, forced timeout and malformed session **PASS**; user's currently open workspace session **NOT VERIFIED**; direct ChatGPT-host attachment **NOT VERIFIED / requires explicit host setup**; `hostConnection=not_verified` must remain unchanged.
- **Next required action:** the owner must open the CHRONO project preview in the Floot editor and bring that tab to the foreground, then ask to continue. Only then can the live DOM/Diagnostics be read and the current pairing ID validated in-place. Do not publish unless an actual defect is identified and the necessary checks pass.


## Live editor follow-up — 2026-10-25 (user confirmed preview open)

- The supported live-preview DOM runner successfully read the currently open Floot preview once. It confirmed the CHRONO workspace and Diagnostics panel are visible, and the displayed realtime bridge status is **CONNECTED**. It also showed the protocol label is still stale (RUN #19, 2026-10-20) and ChatGPT host connection still reads **HOST SETUP REQUIRED**.
- The live DOM result contained a pairing UUID, but it was not copied into the memo or exposed in this note. No command was sent using it.
- A second read-only DOM check intended to validate the pairing ID against the browser's current localStorage and capture the diagnostics labels queued, but the browser disconnected mid-execution before returning a result. Therefore the UUID-to-localStorage match and a command/ACK round trip in the owner's own tab remain **NOT VERIFIED**.
- No app source was changed and no deployment was made. Keep hostConnection=not_verified; the visible CONNECTED status refers only to the app's Realtime bridge, not ChatGPT host connectivity.
- **Next action:** bring the Floot editor/preview tab to the foreground again and rerun the read-only DOM check. If it remains connected, validate the session ID in-place and use an explicitly authorized MCP test path; do not put the ID or any bearer secret in a public file. Do not claim the personal-session end-to-end test passed until an actual command is accepted/rejected by the workspace and the MCP call receives its matching stored acknowledgement.


## Superpowers verification follow-up — 2026-10-25 (UTC)

- Invoked the Superpowers systematic-debugging workflow. No source changes were made because the live-session failure could not be reproduced while the user's Floot editor tab was unavailable.
- Re-ran the targeted Floot Jasmine suite: `helpers/mcpEndpoint.spec.tsx`, `helpers/browserControlAck.spec.tsx`, and `helpers/mcpStatusEndpoint.spec.tsx` — **3 passed, 0 failed**.
- Re-ran targeted TypeScript checks for the page, session helper, realtime channel/provider, MCP endpoint, and ACK endpoint — **clean**.
- Rechecked publish status: app remains published at `https://chrono-cross-gpt.floot.app`; plan is **free**; no publish or paid action was performed.
- Retried the supported live DOM runner; it reported no open Floot tab picked up the code before timeout. Therefore the current owner-session UUID, live command delivery, and matching ACK remain **NOT VERIFIED**. This tool failure does not prove a source defect.
- **Next step:** open the CHRONO preview in Floot and keep that tab in the foreground, then retry the read-only DOM/session validation. Do not send a command, change `hostConnection`, or publish until the current session is verified and an actual matching ACK is observed.


## User-provided workspace snapshot — 2026-10-25 (UTC)

- The user supplied a fresh text snapshot of the CHRONO workspace showing the browser view on `example.com`, Diagnostics visible, Realtime browser bridge `CONNECTED`, MCP token configuration `CONFIGURED`, production protocol label `STALE · RUN #19 · 2026-10-20`, and ChatGPT host connection `HOST SETUP REQUIRED`.
- The snapshot visibly contains a pairing ID in UUID format, but this is user-provided screen text, not a fresh read from the running app DOM or localStorage. The value was not copied into this memo.
- Retried the canonical live DOM runner after receiving the snapshot; it returned `no browser picked up the code within the timeout`, indicating the tool could not reach the user's active Floot tab. No command was sent, no code changed, and no publish occurred.
- Current-session localStorage match, command execution, and matching stored ACK remain **NOT VERIFIED**. The displayed Realtime `CONNECTED` status is not proof of ChatGPT host connection. Keep `hostConnection=not_verified`.
- **Next action:** restore the Floot editor preview tab to the foreground so the canonical runner can execute inside that tab. Then validate the displayed pairing ID against the page's own localStorage in-place, and only after that use an authorized test route that can return a matching ACK without writing the session ID to public files.


## Foreground-runner retry and session storage inspection — 2026-10-25 (UTC)

- After the user asked to continue, retried the canonical live-preview DOM runner once. It again returned `no browser picked up the code within the timeout`. The script did not execute in the user's page; no live DOM or localStorage value was read, and no MCP command was sent.
- Read-only source inspection of published project version `1792659934587` confirms `helpers/browserControl.tsx` uses localStorage key `chrono.browser-control.session.v1`; `getBrowserControlSessionId()` reuses a stored value when valid, otherwise creates and stores a new ID, with an in-memory fallback if storage access throws. `pages/_index.tsx` obtains the ID on mount and subscribes to the matching `chrono-control:<sessionId>` channel. The Realtime token endpoint grants that channel only.
- This establishes the exact check needed next, but does **not** establish the value or state in the owner's active browser. A storage-blocked/in-memory fallback or a stale tab could produce a session mismatch, but neither is confirmed as the cause.
- No app source was changed, no publish occurred, and no session ID or secret was read into the memo. Personal-session command/ACK and direct ChatGPT-host attachment remain **NOT VERIFIED**; keep `hostConnection=not_verified`.
- **Next action:** make the Floot editor preview available in the foreground so the canonical runner can read the live page. It must compare the Diagnostics session ID against the current localStorage entry in-place and return only a match boolean plus storage availability; do not print the ID. Send no command until that check succeeds.
