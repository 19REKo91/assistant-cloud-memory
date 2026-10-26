#!/usr/bin/env node
// Free GitHub Actions → authenticated MCP → one paired CHRONO workspace.
// The request file is public because this repository is public: use only public URLs.
// Never log the bearer token or the pairing-session secret.

import { readFile } from "node:fs/promises";

const ENDPOINT = "https://chrono-cross-gpt.floot.app/_api/mcp";
const REQUEST_PATH = new URL("./chrono-browser-command.json", import.meta.url);
const TOKEN = process.env.CHRONO_MCP_TOKEN || "";
const SESSION_ID = process.env.CHRONO_BROWSER_SESSION_ID || "";
const VERSION = "2025-11-25";

function stop(stage, reason) {
  console.error(JSON.stringify({ ok: false, stage, reason, credentialPrinted: false }, null, 2));
  process.exit(1);
}

function isUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function publicUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error("url_invalid");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") throw new Error("url_scheme_blocked");
  if (url.username || url.password) throw new Error("url_credentials_blocked");
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  const blockedSuffixes = [".localhost", ".local", ".internal", ".test", ".invalid", ".example"];
  if (!host.includes(".") || host === "localhost" || host === "metadata.google.internal" || blockedSuffixes.some((suffix) => host.endsWith(suffix))) {
    throw new Error("non_public_hostname_blocked");
  }
  if (host.includes(":") || /^(?:\d{1,3}\.){3}\d{1,3}$/.test(host)) throw new Error("ip_literal_blocked");
  if (url.port && url.port !== "80" && url.port !== "443") throw new Error("nonstandard_port_blocked");
  for (const key of url.searchParams.keys()) {
    if (/(?:access[_-]?token|api[_-]?key|auth|authorization|code|password|secret|session|token)/i.test(key)) {
      throw new Error("sensitive_query_parameter_blocked");
    }
  }
  url.hash = "";
  return url.toString();
}

function parseResponseBody(text, contentType = "") {
  if (!text) return null;
  if (contentType.toLowerCase().includes("text/event-stream")) {
    for (const event of text.split(/\r?\n\r?\n/)) {
      const data = event.split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""));
      if (!data.length) continue;
      try {
        const parsed = JSON.parse(data.join("\n"));
        if (parsed && typeof parsed === "object" && ("result" in parsed || "error" in parsed)) return parsed;
      } catch { /* Ignore non-JSON SSE events. */ }
    }
    return null;
  }
  try { return JSON.parse(text); } catch { return null; }
}

async function post(method, id, params, protocolVersion) {
  let response;
  try {
    response = await fetch(ENDPOINT, {
      method: "POST",
      redirect: "error",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + TOKEN,
        ...(protocolVersion ? { "MCP-Protocol-Version": protocolVersion } : {}),
      },
      body: JSON.stringify({ jsonrpc: "2.0", ...(id === undefined ? {} : { id }), method, ...(params === undefined ? {} : { params }) }),
    });
  } catch {
    stop(method, "network_request_failed");
  }
  const text = await response.text();
  const body = parseResponseBody(text, response.headers.get("content-type") || "");
  if (response.status >= 400 || !body) stop(method, "http_or_protocol_error");
  if (body.error) stop(method, "mcp_method_rejected");
  return { response, body };
}

let request;
try {
  request = JSON.parse(await readFile(REQUEST_PATH, "utf8"));
} catch {
  stop("request_file", "cannot_read_command_json");
}

if (!request || typeof request !== "object" || Array.isArray(request)) stop("request_file", "invalid_command_shape");
if (request.enabled !== true) {
  console.log(JSON.stringify({ ok: true, status: "skipped", reason: "command_disabled", credentialPrinted: false }, null, 2));
  process.exit(0);
}
if (typeof request.requestId !== "string" || !/^[A-Za-z0-9._-]{1,80}$/.test(request.requestId)) stop("request_file", "invalid_request_id");
if (!["navigate", "new_tab", "select_tab"].includes(request.action)) stop("request_file", "unsupported_action");
if (TOKEN.length < 32 || /\s/.test(TOKEN)) stop("secrets", "CHRONO_MCP_TOKEN_missing_or_malformed");
if (!isUuid(SESSION_ID)) stop("secrets", "CHRONO_BROWSER_SESSION_ID_missing_or_malformed");

const args = { sessionId: SESSION_ID, action: request.action };
if (request.action === "navigate") {
  if (typeof request.url !== "string" || request.url.length > 2048) stop("request_file", "navigate_requires_url");
  try {
    args.url = publicUrl(request.url);
  } catch (error) {
    stop("request_file", error instanceof Error ? error.message : "url_validation_failed");
  }
} else if (request.action === "select_tab") {
  if (!Number.isSafeInteger(request.tabId) || request.tabId < 1) stop("request_file", "select_tab_requires_positive_tab_id");
  args.tabId = request.tabId;
}

const init = await post("initialize", 1, {
  protocolVersion: VERSION,
  capabilities: {},
  clientInfo: { name: "chrono-github-actions-bridge", version: "1.0.0" },
});
if (init.response.status !== 200 || init.body?.jsonrpc !== "2.0" || init.body?.id !== 1 || init.body?.result?.serverInfo?.name !== "chrono-cross-gpt" || init.body?.result?.protocolVersion !== VERSION) {
  stop("initialize", "unexpected_mcp_initialize_response");
}
const negotiatedVersion = init.body.result.protocolVersion;

let notification;
try {
  notification = await fetch(ENDPOINT, {
    method: "POST",
    redirect: "error",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Authorization": "Bearer " + TOKEN,
      "MCP-Protocol-Version": negotiatedVersion,
    },
    body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }),
  });
} catch {
  stop("notifications/initialized", "network_request_failed");
}
if (notification.status !== 202 || (await notification.text()).trim() !== "") stop("notifications/initialized", "unexpected_notification_response");

const listed = await post("tools/list", 2, undefined, negotiatedVersion);
const toolNames = listed.body?.result?.tools?.map((tool) => tool?.name) || [];
if (listed.response.status !== 200 || listed.body?.jsonrpc !== "2.0" || listed.body?.id !== 2 || !toolNames.includes("control_browser_workspace")) {
  stop("tools/list", "required_control_tool_not_available");
}

const call = await post("tools/call", 3, { name: "control_browser_workspace", arguments: args }, negotiatedVersion);
const result = call.body?.result;
const meta = result?.structuredContent;
if (call.response.status !== 200 || call.body?.jsonrpc !== "2.0" || call.body?.id !== 3 || result?.isError === true || meta?.acknowledged !== true || meta?.acknowledgementStatus !== "acknowledged") {
  const diagnostic = {
    httpStatus: call.response.status,
    jsonrpcValid: call.body?.jsonrpc === "2.0",
    responseIdValid: call.body?.id === 3,
    toolReportedError: result?.isError === true,
    structuredContentKeys: meta && typeof meta === "object" ? Object.keys(meta).slice(0, 20) : [],
    acknowledged: meta?.acknowledged === true,
    acknowledgementStatus: typeof meta?.acknowledgementStatus === "string" ? meta.acknowledgementStatus.slice(0, 40) : null,
    contentItemTypes: Array.isArray(result?.content) ? result.content.map((item) => item?.type).slice(0, 5) : [],
    credentialPrinted: false,
  };
  stop("control_browser_workspace", "command_not_acknowledged:" + JSON.stringify(diagnostic));
}

console.log(JSON.stringify({
  ok: true,
  status: "acknowledged",
  requestId: request.requestId,
  action: request.action,
  deliveryCount: meta.deliveryCount,
  acknowledgementStatus: meta.acknowledgementStatus,
  pageLoadVerified: meta.pageLoadVerified === true,
  commandId: meta.commandId,
  credentialPrinted: false,
}, null, 2));
