# CHRONO CROSS GPT — Follow-up Work Memo
Date: 2026-10-22 (UTC)
Repository: `19REKo91/assistant-cloud-memory`
Branch: `main`

## Verified outcomes

### Offline MCP test suite
- **PASS** — GitHub Actions run [39843516397](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39843516397)
- Commit: `0168057ce85b1698ba8f2b8a9dda6130b9a30d83`
- All workflow checks passed: MCP JSON and allowlists, Copilot custom-agent YAML, workflow trigger validation, smoke-test syntax, and offline mock tests.
- The mock covers initialization, initialized notification, tool listing/calls, SSE response parsing, authentication rejection, protocol response identity, URL safety, and redaction.

### Production MCP handshake
- **PASS** — GitHub Actions run [39843509619](https://github.com/19REKo91/assistant-cloud-memory/actions/runs/39843509619)
- Smoke-test commit: `3ef3965ace2d999a5c981890b02192ce904cd5f7`
- Authenticated `initialize`: HTTP 200, MCP protocol `2025-11-25`.
- `notifications/initialized`: HTTP 202.
- `tools/list`: HTTP 200.
- Tool calls to `get_browser_capabilities` and `read_public_page`: HTTP 200 and passed the deployed endpoint's response checks.
- Missing and invalid bearer tokens were rejected. Tested unsafe URLs (private IP, noncanonical loopback, file URL, embedded credentials, nonstandard port, oversized URL) were rejected.
- Logs explicitly reported `credentialPrinted: false`; no token value was recorded in this memo.

### Changes made
- `tools/test-chrono-cross-gpt-mcp-smoke-test.mjs`: repaired mock syntax and updated its fixture to match the public-page reader's returned text.
- `tools/chrono-cross-gpt-mcp-smoke-test.mjs`: corrected the production page assertion to validate the actual deployed response. The earlier assertion falsely expected a literal “Example Domain” heading and structured metadata, while the live reader wraps page text with an “UNTRUSTED PUBLIC WEB CONTENT” notice.

## Remaining gap — highest priority
- **Not complete:** the production MCP server still lists only `read_public_page` and `get_browser_capabilities`.
- **Not verified:** live browser-tab control, DOM interaction, external browser session control, or direct connection to the current ChatGPT Android session.
- A separate browser-control/acknowledgement implementation exists in the Floot working copy according to the prior project log, but it is **not published** and its full UI → MCP command → acknowledgement round trip remains unverified.
- Therefore, the successful production handshake proves MCP protocol/authentication/public-page reading only; it does not prove real browser control.
- Back/Forward is intentionally deferred, per the user's instruction.

## Next steps
1. Preserve the passing production and offline checks.
2. When Floot build actions are available, inspect the current preview and test the unpublished paired-workspace control command end-to-end: accepted, rejected, timeout, and no-listener cases.
3. Publish only after preview verification; then ensure the deployed MCP tool list and client allowlists actually include the verified browser-control tool.
4. Re-run the production handshake and check the actual tool list and control acknowledgement result.
5. Keep direct ChatGPT-host integration marked **unverified** until configured and tested with a real client. Never ask for or expose the bearer token.

## Status
- Offline tests: **COMPLETE / PASS** for the current test harness.
- Production MCP protocol and public-page smoke test: **COMPLETE / PASS** for the currently deployed two-tool endpoint.
- Actual browser control and ChatGPT-session integration: **INCOMPLETE**; deployment and end-to-end evidence are still missing.

## Client-integration boundary and current blocker (verified 2026-10-22)
- The repository's `.vscode/mcp.json` is a VS Code MCP configuration using a password prompt. `.github/agents/chrono-cross-gpt-reader.agent.md` targets `github-copilot` and references the GitHub Copilot Agents secret `COPILOT_MCP_CHRONO_TOKEN`. These files configure VS Code / GitHub Copilot clients; they do not configure the user's ChatGPT Android app session.
- The deployed server's verified tool list is still read-only: `read_public_page` and `get_browser_capabilities`. The unpublished browser-control implementation cannot become active in production until it is validated and deliberately published.
- Floot confirmed the free account's daily build-action quota is exhausted and resets at **2026-10-23 07:00 UTC (10:00 AM Baghdad time)**. Read-only publish-status checking remains available; project code-reading/testing/editing actions are paused until reset. No paid action was taken and no production publish was attempted.
- Until Floot actions reset, safe progress is limited to GitHub-side review and documentation. Next session should resume with the Floot preview round-trip test—not another change to Back/Forward—and must verify accepted/rejected/timeout/no-listener outcomes before considering publication.
