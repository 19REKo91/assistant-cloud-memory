# CHRONO CROSS GPT — Playwright contingency design

**Date:** 2026-10-26  
**Status:** Prepared as a contingency only; not approved for implementation and not executed.

## Intent

Keep the current CHRONO MCP + Realtime browser-control bridge as the primary path. Prepare a low-risk fallback based on Microsoft's Playwright MCP / Playwright browser automation only if the current browser-control path fails its defined verification gates. The fallback must not displace working code merely because another tool is available.

## Current evidence

- A live public navigation command was acknowledged and persisted by the current workspace bridge (nav-example-004, https://example.com/); its recorded pageLoadVerified value was false.
- The matching iframe-load-receipt draft is unpublished and unverified. Its documented TypeScript blocker is the missing ackPromise on the pending-navigation object. It must be corrected and tested before any publish.
- GitHub Actions has successfully run a disposable Playwright/Chromium browser E2E. That proves the isolated test-browser path, not control of the user's mobile browser.
- The app's MCP host status must remain not_verified until a genuine host handshake is proven.
- OpenAI's current Help Center says custom MCP servers cannot be connected from ChatGPT mobile; this ChatGPT Free Android environment therefore has a separate host-availability blocker. Switching the browser engine will not remove that limitation. See https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt.

## Goals

1. Preserve the current implementation and its history as the primary route.
2. Have a documented, test-first fallback that can provide reliable remote-browser navigation, accessibility/DOM snapshots, clicks, form fills, and observable results.
3. Keep a stable, narrow MCP-facing interface where feasible, so the UI/client need not be rewritten.
4. Distinguish command acceptance, navigation request, matching frame-load event, page-content readability, and ChatGPT-host connectivity as separate states.
5. Use free/open-source options only; verify current host limits and do not incur charges or require a paid upgrade.
6. Provide an explicit rollback path and never enable the fallback automatically in production.

## Non-goals and limits

- No implementation, dependency installation, source changes, workflow changes, publication, or production switch is authorized by this design document.
- This fallback does not promise control over the user's Android browser, its cookies, or the ChatGPT mobile app.
- A dedicated Playwright browser is a separate browser session unless a supported, explicit session-bridging design is proven. Do not imply it shares the user's signed-in browser.
- Do not pass the production bearer token or browser pairing/session IDs to third-party hosted inspectors or public logs.
- Do not use private URLs or private account content in public-repository test commands.

## Approaches considered

### A. Keep the current bridge as primary — selected

Finish the existing ACK-before-load-receipt work, test it, and verify the public test navigation. This preserves the work already done and addresses the current evidence gap directly.

### B. Add a Playwright-backed remote browser worker as a fallback — selected contingency

Evaluate the official Microsoft Playwright MCP server (https://github.com/microsoft/playwright-mcp) and its currently supported transport/hosting requirements. If it can be exposed securely within a verified no-cost environment, connect it behind a separate, disabled-by-default adapter or route. If its MCP transport cannot run in the chosen host, consider a narrow Playwright-library worker instead; do not assume stdio MCP automatically provides a remote HTTP endpoint.

This can improve browser automation in a dedicated remote session. It does not by itself connect ChatGPT Free on Android to a custom MCP server.

### C. Replace the current bridge now — rejected

A full replacement is premature: the current bridge already acknowledged a real workspace command, and the remaining uncertainties have not established that the whole architecture is unworkable. Immediate replacement creates avoidable regression risk.

## Fallback activation gates

Do not activate the fallback until the current-path work has been re-read, repaired, and tested. Consider the browser-worker fallback only if either:

- after a clean typecheck and relevant tests, two controlled, harmless public-navigation checks still cannot produce correlated command acknowledgement plus the matching expected load/event evidence; or
- investigation proves a required browser capability cannot be implemented reliably in the current hosted runtime.

Before counting a failure, verify only safe booleans/statuses for the active workspace; never print the session ID or bearer token.

**Separate host gate:** If the only blocker is that ChatGPT Free on Android cannot attach to custom MCP servers, do not treat that as evidence the browser bridge failed. Pause the engine migration and record that a supported host/client is still required. No Playwright replacement can grant unsupported host permissions.

## Acceptance criteria for any future fallback

- Runs in an isolated development/staging context first; production path remains unchanged.
- Exposes only required browser actions and validates every input.
- Accepts HTTPS public URLs for initial validation; rejects unsafe schemes, localhost/private-network targets, credential-bearing URLs, and malformed inputs.
- A harmless test page can be navigated, snapshotted, and interacted with in a controlled fixture; observed outcome is returned with a request/session correlation ID that is not a secret.
- Negative tests cover missing/invalid authentication, timeout, duplicate requests, malformed payloads, unsafe URLs, and unavailable browser runtime.
- Results separately report action accepted, navigation result, snapshot/result available, and host connection. Never infer page usability from an iframe onLoad signal alone.
- Secrets are never printed, committed, placed in URLs, or sent to unreviewed third-party services.
- Free hosting is checked at implementation time; no account/payment/upgrade action is taken without the user's explicit authorization.
- Rollback to the current bridge is documented and tested before any production switch.
- A human-reviewed comparison shows the fallback works materially better for the actual target scenario.

## Decision

**Superpowers recommendation:** maintain the current bridge as primary. Prepare Playwright as a staged contingency—not as an immediate replacement. First finish the known ackPromise / load-receipt validation. If the browser-engine path still fails, test the fallback separately. If the real blocker remains ChatGPT host availability on Android Free, stop: the issue is host compatibility, not which browser MCP engine is used.
