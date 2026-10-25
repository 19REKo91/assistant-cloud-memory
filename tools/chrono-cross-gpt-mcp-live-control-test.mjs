#!/usr/bin/env node
// Real production browser-control round-trip test.
// The pairing UUID is read from a disposable Playwright browser context and is never logged or persisted.
import { chromium } from "playwright";

const ENDPOINT = "https://chrono-cross-gpt.floot.app/_api/mcp";
const APP_URL = "https://chrono-cross-gpt.floot.app/";
const token = process.env.CHRONO_MCP_TOKEN;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

let stage = "configuration";
let failureReason = "";
let browser;
let protocolVersion = "";
let rpcId = 20;

function check(condition, reason) {
  if (!condition) {
    failureReason = reason;
    throw new Error("LIVE_CONTROL_TEST_FAILED");
  }
}

function parseBody(body, contentType) {
  if (!body) return null;
  if ((contentType || "").toLowerCase().includes("text/event-stream")) {
    for (const event of body.split(/\r?\n\r?\n/)) {
      const data = event.split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""));
      if (!data.length) continue;
      try {
        const value = JSON.parse(data.join("\n"));
        if (value && typeof value === "object" && ("result" in value || "error" in value)) return value;
      } catch {}
    }
    return null;
  }
  try { return JSON.parse(body); } catch { return null; }
}

async function rpc(method, id, params, version) {
  const message = { jsonrpc: "2.0", method };
  if (id !== undefined) message.id = id;
  if (params !== undefined) message.params = params;
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": "Bearer " + token,
  };
  if (version) headers["MCP-Protocol-Version"] = version;
  const response = await fetch(ENDPOINT, {
    method: "POST",
    redirect: "error",
    headers,
    body: JSON.stringify(message),
  });
  const body = await response.text();
  return {
    status: response.status,
    parsed: parseBody(body, response.headers.get("content-type") || ""),
  };
}

async function callTool(name, args) {
  const id = rpcId++;
  const response = await rpc("tools/call", id, { name, arguments: args }, protocolVersion);
  check(response.status === 200, name + ": unexpected HTTP status");
  check(response.parsed?.jsonrpc === "2.0" && response.parsed?.id === id && response.parsed?.result,
    name + ": invalid JSON-RPC response");
  return response.parsed.result;
}

function textContent(result) {
  return Array.isArray(result?.content)
    ? result.content.filter((item) => item?.type === "text").map((item) => item.text || "").join("\n")
    : "";
}

async function waitForFrame(page, expectedUrl) {
  await page.waitForFunction((target) => {
    const frames = Array.from(document.querySelectorAll('iframe[title^="Browser view of"]'));
    return frames.some((frame) => frame.getAttribute("src") === target);
  }, expectedUrl, { timeout: 12000 });
}

try {
  check(typeof token === "string" && token.length >= 32 && !/\s/.test(token),
    "CHRONO_MCP_TOKEN is missing or malformed; value not printed");

  stage = "launching-disposable-browser";
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(12000);

  stage = "opening-production-workspace";
  await page.goto(APP_URL, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForFunction(() => {
    const label = Array.from(document.querySelectorAll("b"))
      .find((element) => element.textContent?.trim() === "MCP PAIRING ID");
    if (!label?.parentElement) return false;
    return Array.from(label.parentElement.querySelectorAll("div"))
      .some((element) => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(element.textContent?.trim() || ""));
  }, null, { timeout: 30000 });

  const sessionId = await page.evaluate(() => {
    const label = Array.from(document.querySelectorAll("b"))
      .find((element) => element.textContent?.trim() === "MCP PAIRING ID");
    if (!label?.parentElement) return "";
    return Array.from(label.parentElement.querySelectorAll("div"))
      .map((element) => element.textContent?.trim() || "")
      .find((value) => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)) || "";
  });
  check(UUID_RE.test(sessionId), "could not read a valid pairing UUID from the current UI");

  stage = "waiting-for-realtime-connection";
  await page.waitForFunction(() => {
    const label = Array.from(document.querySelectorAll("span"))
      .find((element) => element.textContent?.trim() === "Realtime browser bridge");
    return label?.parentElement?.querySelector("b")?.textContent?.trim() === "CONNECTED";
  }, null, { timeout: 30000 });
  // Let the React channel subscription run after the WebSocket becomes connected.
  await new Promise((resolve) => setTimeout(resolve, 1200));

  stage = "mcp-initialize";
  const init = await rpc("initialize", 1, {
    protocolVersion: "2025-11-25",
    capabilities: {},
    clientInfo: { name: "chrono-live-control-e2e", version: "1.0.0" },
  });
  check(init.status === 200 && init.parsed?.jsonrpc === "2.0" && init.parsed?.id === 1 &&
    init.parsed?.result?.serverInfo?.name === "chrono-cross-gpt",
    "production MCP initialize failed");
  protocolVersion = init.parsed.result.protocolVersion;
  check(protocolVersion === "2025-11-25", "unexpected negotiated MCP protocol version");

  stage = "mcp-initialized-notification";
  const initialized = await rpc("notifications/initialized", undefined, undefined, protocolVersion);
  check(initialized.status === 202, "MCP initialized notification failed");

  stage = "live-navigation-and-ack";
  const navigationUrl = "https://example.com/?chrono_e2e=" + Date.now();
  const navigation = await callTool("control_browser_workspace", {
    sessionId,
    action: "navigate",
    url: navigationUrl,
  });
  const navigationMeta = navigation?.structuredContent;
  check(navigation?.isError !== true && navigationMeta?.acknowledged === true &&
    navigationMeta?.acknowledgementStatus === "acknowledged" &&
    navigationMeta?.action === "navigate" && Number(navigationMeta?.deliveryCount) >= 1,
    "live navigation did not return a trusted acknowledgement");
  await waitForFrame(page, navigationUrl);

  stage = "ui-acknowledgement-record";
  await page.getByRole("button", { name: "Activity", exact: true }).click();
  await page.waitForFunction((commandId) => {
    const content = document.body.innerText;
    return content.includes("MCP acknowledgement stored") && content.includes(commandId);
  }, navigationMeta.commandId, { timeout: 10000 });

  stage = "live-explicit-rejection";
  const rejection = await callTool("control_browser_workspace", {
    sessionId,
    action: "select_tab",
    tabId: 999999,
  });
  const rejectionMeta = rejection?.structuredContent;
  check(rejection?.isError === true && rejectionMeta?.acknowledgementStatus === "rejected" &&
    rejectionMeta?.acknowledged === false,
    "live invalid-tab command was not explicitly rejected");
  await page.waitForFunction(() => document.body.innerText.includes("MCP tab selection rejected"),
    null, { timeout: 10000 });

  stage = "live-acknowledgement-timeout";
  await page.route("**/_api/browser-control-ack", (route) => route.abort());
  const timeoutUrl = "https://example.com/?chrono_e2e_timeout=" + Date.now();
  let timeoutResult;
  try {
    timeoutResult = await callTool("control_browser_workspace", {
      sessionId,
      action: "navigate",
      url: timeoutUrl,
    });
  } finally {
    await page.unroute("**/_api/browser-control-ack");
  }
  const timeoutMeta = timeoutResult?.structuredContent;
  check(timeoutResult?.isError === true && timeoutMeta?.acknowledged === false &&
    timeoutMeta?.acknowledgementStatus === "timeout",
    "blocked acknowledgement did not produce the expected timeout result");
  await waitForFrame(page, timeoutUrl);

  stage = "live-invalid-session";
  const invalidSession = await callTool("control_browser_workspace", {
    sessionId: "not-a-uuid",
    action: "navigate",
    url: "https://example.com/",
  });
  check(invalidSession?.isError === true &&
    textContent(invalidSession).includes("sessionId must be the UUID shown"),
    "invalid session ID was not rejected before dispatch");

  console.log(JSON.stringify({
    ok: true,
    liveNavigation: {
      status: "PASS",
      mcpAcknowledgement: "acknowledged",
      uiNavigationApplied: true,
      uiAcknowledgementStored: true,
      deliveryCount: navigationMeta.deliveryCount,
    },
    explicitRejection: { status: "PASS", acknowledgementStatus: rejectionMeta.acknowledgementStatus },
    acknowledgementTimeout: { status: "PASS", acknowledgementStatus: timeoutMeta.acknowledgementStatus },
    invalidSession: { status: "PASS", rejectedBeforeDispatch: true },
    sessionIdLogged: false,
    credentialPrinted: false,
  }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    stage,
    reason: failureReason || "browser or network operation failed; sensitive values were not printed",
    errorType: error instanceof Error ? error.name : "unknown",
    sessionIdLogged: false,
    credentialPrinted: false,
  }, null, 2));
  process.exitCode = 1;
} finally {
  if (browser) {
    try { await browser.close(); } catch {}
  }
}
