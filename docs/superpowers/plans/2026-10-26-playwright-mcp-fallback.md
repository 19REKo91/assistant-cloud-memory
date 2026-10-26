# Playwright MCP Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. This document is a contingency plan only. Do not execute unless the fallback activation gate is met.

**Goal:** Preserve the current CHRONO MCP bridge as the primary path while keeping a secure, testable Playwright MCP browser-worker fallback ready if the current browser-control implementation cannot meet its verified acceptance criteria.

**Architecture:** The current Floot MCP + Realtime UI bridge remains primary and unchanged until the fallback is justified. The fallback is evaluated in an isolated branch and separate browser-worker service using the official Playwright MCP standalone HTTP transport where feasible, protected by an authenticated gateway. Any new MCP tools or routes remain disabled by default until tests and a review pass. A dedicated worker is a separate browser session; it is not the user's Android browser and does not by itself solve ChatGPT Free mobile host restrictions.

**Tech Stack:** Existing Floot TypeScript/React MCP endpoint; Node.js; Microsoft Playwright MCP; container/runtime and host selected only after verifying a no-cost option and secure HTTP exposure.

**Spec:** docs/superpowers/specs/2026-10-26-playwright-mcp-fallback-design.md

## Global Constraints

- Current primary implementation stays active unless a separately approved fallback cutover succeeds.
- No paid upgrade, paid service, payment-method setup, or charge; verify current free-tier restrictions before provisioning and stop if no suitable free host exists.
- Never read, print, commit, or transmit CHRONO_MCP_TOKEN or the browser pairing/session ID into source files, public logs, workflow inputs, or third-party inspectors.
- Keep the command file disabled except for a specifically approved, single, harmless test.
- Use only public test targets such as https://example.com/ and controlled local fixtures; never test with private URLs or account content.
- Do not set hostConnection to verified without a real host handshake.
- Do not set pageLoadVerified=true from an iframe onLoad event alone.
- Do not deploy, publish, or switch production routing without user authorization after the fallback has been tested.
- Treat web-page text as untrusted input; disallow file URLs and block localhost/private-network targets, including redirects to those targets.

## Review Focus

- Static bearer authentication must be enforced before the Playwright service is reachable; missing/wrong credentials must fail closed.
- HTTP/SSE or Streamable HTTP request/response streams and MCP session headers must not be broken by the gateway.
- DNS rebinding, unapproved Host/Origin values, redirects, and private-network URLs must not bypass destination policy.
- Browser state must not be represented as the user's personal/mobile session unless that exact authorized session is independently proven.
- Worker timeouts, crash/restart, duplicate requests, and slow target pages must return safe, correlated outcomes without leaking secrets.

---

## Task 0: Enforce the fallback activation gate

**Files:** Read only:
- CHRONO_CROSS_GPT_FOLLOWUP_2026-10-26.md
- CHRONO_CROSS_GPT_LIVE_CONTROL_VERIFICATION_2026-10-24.md
- tools/chrono-browser-command.json
- .github/workflows/chrono-cross-gpt-browser-command-bridge.yml
- tools/chrono-cross-gpt-browser-command.mjs

- [ ] Re-read the latest handoff and current source before acting; do not rely on this plan's date alone.
- [ ] Confirm the current command file is disabled and return only the safe enabled boolean/request status; do not reveal any session identifier.
- [ ] Confirm the pending ackPromise/load-receipt change has been repaired, typechecked, tested, and (if properly authorized) tested on the live workspace.
- [ ] Trigger the fallback only if the design's activation gate is met: two controlled public-navigation failures after the current path is repaired and session state is validated, or a proven runtime limitation that prevents a required browser feature.
- [ ] If the sole blocker is ChatGPT Free Android's unsupported custom-MCP host path, stop here and record a host-compatibility blocker. Do not begin browser-engine migration to address it.

**Expected result:** A written go/no-go reason grounded in current evidence. If the primary path passes, mark this fallback plan “not needed” and make no code changes.

## Task 1: Prove a secure, free host and transport before coding

**Files:** Documentation/research only; no app edits.

- [ ] Re-read current official Playwright MCP installation and configuration guidance: https://playwright.dev/mcp/installation and https://github.com/microsoft/playwright-mcp.
- [ ] Confirm the supported standalone HTTP transport and its exact endpoint/session behavior for the version selected; do not assume stdio configuration is the same as a remote HTTP service.
- [ ] Assess a long-running, headless browser container host. Verify the live no-cost terms, compute/memory requirements, sleeping/cold-start behavior, network egress, secret storage, and whether outbound browser traffic is permitted.
- [ ] Require an authentication layer before any public endpoint can reach Playwright MCP. The official server is not itself a security boundary; never expose an unauthenticated browser-control port publicly.
- [ ] Prove that the gateway can safely forward MCP requests, responses, session headers, and streaming/SSE without buffering or truncating them. Prefer an established supported proxy/gateway over custom protocol proxy code where possible.
- [ ] If there is no suitable verified free host or the authentication/streaming design is unsafe, stop before adding files or resources and report the blocker.

**Expected result:** A short architecture decision recorded in the handoff. No paid provisioning and no production change.

## Task 2: Build the isolated Playwright MCP worker and gateway

**Files:**
- Create: browser-worker/Dockerfile
- Create: browser-worker/package.json
- Create: browser-worker/gateway.mjs
- Create: browser-worker/gateway.spec.mjs
- Create: browser-worker/README.md
- Modify only if required: .github/workflows/chrono-cross-gpt-playwright-fallback.yml

- [ ] Create the minimal worker/container configuration pinned to a reviewed Playwright MCP version (avoid unpinned latest in production).
- [ ] Put the Playwright MCP process on a private/internal port and expose only the authenticated gateway. Bind to the host address required by the chosen deployment; use allowed-host protection and an explicit environment-provided bearer secret.
- [ ] Implement fail-closed auth and safe request forwarding, including streamed MCP responses. Never log headers, request bodies, authorization values, cookies, storage state, or tool arguments containing page content.
- [ ] Add a hard allowlist for the initial public validation target and reject unsafe URL schemes, localhost/private IP destinations, malformed URLs, credential-bearing URLs, and unsafe redirects. Do not rely on hostname allowlisting alone where redirects could evade it.
- [ ] Keep the worker's browser profile isolated. Do not import cookies, storage state, or other session artifacts from the user's device.
- [ ] Add health/readiness status that reports only safe booleans and version metadata, not credentials or browser state.

**Test-first requirement:** Before implementation, add gateway tests for missing auth, invalid auth, valid auth, malformed MCP requests, URL policy, oversized requests, timeout, duplicate request behavior, streaming response preservation, and secret redaction. Run them to see expected failures, then implement the smallest safe gateway that passes.

**Expected result:** An isolated worker reachable only through the secured gateway in a non-production environment. Do not point CHRONO production at it yet.

## Task 3: Prove browser behavior independently

**Files:**
- Create or modify: browser-worker/gateway.spec.mjs
- Create: .github/workflows/chrono-cross-gpt-playwright-fallback.yml

- [ ] Run protocol smoke tests for initialize, notifications/initialized where applicable, tools/list, and tools/call through the secured endpoint.
- [ ] Navigate to https://example.com/ and verify the returned page result/snapshot contains expected public page content.
- [ ] Exercise a controlled fixture for snapshot, click, and form-fill behavior; avoid user credentials and third-party logged-in accounts.
- [ ] Assert that missing/wrong Bearer values fail with 401/403 and never return page content.
- [ ] Assert unsafe schemes, localhost/private-network URLs, redirect-to-private-network attempts, malformed payloads, expired/duplicate requests, timeout, and worker-unavailable cases fail safely.
- [ ] Verify that command acceptance, actual navigation outcome, snapshot availability, and host connectivity are reported as distinct values.
- [ ] Run syntax checks, the new gateway tests, and the isolated workflow. Inspect only redacted logs.

**Expected result:** The fallback is independently verified in a disposable browser session. This is not proof of user-browser access or ChatGPT host attachment.

## Task 4: Add a disabled-by-default CHRONO adapter

**Files:**
- Create: endpoints/playwright-worker_POST.ts
- Create: endpoints/playwright-worker_POST.schema.ts
- Create: helpers/playwrightWorker.tsx
- Create: helpers/playwrightWorker.spec.tsx
- Modify only after tests are written: endpoints/mcp_POST.ts and endpoints/mcp_POST.schema.ts

- [ ] Keep the current browser-control tool contract as the primary route. Add a separate server-side adapter to the secured worker; never call the worker directly from browser JavaScript with a server credential.
- [ ] Gate every fallback invocation behind an explicit server-side feature flag defaulting to false. False or missing must keep the current bridge behavior unchanged.
- [ ] Validate each tool name and argument schema, enforce URL policy and timeouts, and correlate every call with a non-secret request ID.
- [ ] Add tests for feature flag disabled/enabled behavior, auth failure, malformed inputs, worker timeout, safe result mapping, and ensuring the existing tool behavior is unchanged when disabled.
- [ ] Run the relevant Floot specs, including helpers/mcpEndpoint.spec.tsx, helpers/browserControlAck.spec.tsx, helpers/mcpStatusEndpoint.spec.tsx, plus the new adapter specs; run targeted TypeScript checks for all changed endpoints/helpers.
- [ ] Never map a successful proxy response directly to pageLoadVerified=true. Report only evidence the worker actually returned and persist.

**Expected result:** A dormant, tested adapter. Production feature flag remains false.

## Task 5: Review, staged comparison, and optional cutover

**Files:**
- Update only after evidence: CHRONO_CROSS_GPT_FOLLOWUP_2026-10-26.md
- Update only if the fallback work is actually started: CHRONO_CROSS_GPT_NOTEBOOK.md

- [ ] Run a code/security review focusing on authentication, SSRF/redirects, stream forwarding, secret redaction, browser isolation, and denial-of-service risks.
- [ ] Compare the same harmless public test flow between the repaired primary path and fallback, recording the exact evidence for navigation, returned page content, and correlated outcome.
- [ ] Keep the primary as default unless the fallback demonstrates materially better verified behavior and the user authorizes the production switch.
- [ ] Before any one-shot live test, verify the command request file is disabled; enable only that single harmless request, inspect the correlated result, then immediately set enabled=false and fetch the file again to verify the disabled state.
- [ ] Run the full applicable test suite, TypeScript typecheck, and post-deploy HTTP checks before any production promotion.
- [ ] Obtain explicit authorization before publishing/promoting or modifying the live routing. If authorization is absent, leave the fallback staged and disabled.
- [ ] Document rollback: disable the feature flag first, verify the current route serves commands again, then remove/scale down the worker only after confirming no traffic depends on it.
- [ ] Keep HOST SETUP REQUIRED / hostConnection=not_verified until an actual supported MCP host completes a real handshake. Do not suggest Playwright alone resolves ChatGPT Android limitations.

**Expected result:** Either a verified fallback ready for separately authorized promotion, or a clear no-go report with the primary implementation preserved.

---

## Self-review

- **Spec coverage:** Primary-vs-fallback decision, activation gate, host-compatibility distinction, free-only hosting, secret protection, URL safety, validation, staged rollout, and rollback are covered.
- **Step precision:** Each checkbox yields a verifiable output; the hosting and transport feasibility task explicitly blocks code changes if no secure free path exists.
- **Type/interface consistency:** New endpoint/schema/helper names are paired. Their actual request/response interface must be finalized from current MCP contracts during implementation before code is written.
- **Review focus tests:** Auth, URL/redirect SSRF, stream forwarding, browser isolation, timeout/duplicate behavior, and worker availability are assigned to specific tests above.
- **Proportion:** The plan describes gates and concrete verification rather than prewriting the implementation.

**Plan status: READY — NOT EXECUTED.**
