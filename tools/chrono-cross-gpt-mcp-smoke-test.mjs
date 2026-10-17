#!/usr/bin/env node
// Safe MCP protocol smoke test. Reads the token only from the process environment.
// It never prints request headers or the token, including when a server echoes it.

const ENDPOINT_TEXT = "https://chrono-cross-gpt.floot.app/_api/mcp";
const token = process.env.CHRONO_MCP_TOKEN;

function stop(message, exitCode = 2) {
  console.error(message);
  process.exit(exitCode);
}

if (typeof token !== "string" || token.length < 32 || /\s/.test(token)) {
  stop("CHRONO_MCP_TOKEN is missing or malformed. Set it in a secure environment; do not put it in chat, a URL, source control, or a command that is saved in shell history.");
}

const endpoint = new URL(ENDPOINT_TEXT);
if (endpoint.protocol !== "https:" || endpoint.hostname !== "chrono-cross-gpt.floot.app" || endpoint.pathname !== "/_api/mcp") {
  stop("Refusing to send credentials to an endpoint outside the verified CHRONO CROSS GPT production origin.");
}

function parseResponseBody(body, contentType = "") {
  if (!body) return null;
  if (contentType.toLowerCase().includes("text/event-stream")) {
    // Streamable HTTP may return the JSON-RPC response inside an SSE data field.
    // Ignore comments, event names, and non-JSON keep-alive events.
    const events = body.split(/\r?\n\r?\n/);
    for (const event of events) {
      const data = event.split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""));
      if (!data.length) continue;
      try {
        const value = JSON.parse(data.join("\n"));
        if (value && typeof value === "object" && ("result" in value || "error" in value)) return value;
      } catch { /* Ignore non-JSON SSE events and continue looking for the JSON-RPC response. */ }
    }
    return null;
  }
  try { return JSON.parse(body); } catch { return null; }
}

async function request(method, id, params, protocolVersion) {
  const message = { jsonrpc: "2.0", method };
  if (id !== undefined) message.id = id;
  if (params !== undefined) message.params = params;
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": `Bearer ${token}`,
  };
  if (protocolVersion) headers["MCP-Protocol-Version"] = protocolVersion;
  const response = await fetch(endpoint, {
    method: "POST",
    redirect: "error",
    headers,
    body: JSON.stringify(message),
  });
  const body = await response.text();
  const redacted = body.split(token).join("[REDACTED]");
  const parsed = parseResponseBody(redacted, response.headers.get("content-type") || "");
  return { response, body: redacted, parsed };
}

function fail(stage, status, body, challenge, diagnostics = undefined) {
  console.error(JSON.stringify({
    ok: false,
    stage,
    httpStatus: status,
    wwwAuthenticate: challenge || null,
    responseExcerpt: (body || "").slice(0, 350) || null,
    diagnostics,
    credentialPrinted: false,
  }, null, 2));
  process.exit(1);
}

async function callTool(name, id, args, protocolVersion) {
  const call = await request("tools/call", id, { name, arguments: args }, protocolVersion);
  const result = call.parsed?.result;
  const textItems = Array.isArray(result?.content)
    ? result.content.filter((item) => item?.type === "text" && typeof item.text === "string" && item.text.trim().length > 0)
    : [];
  const hasStructuredContent = !!result?.structuredContent && typeof result.structuredContent === "object";
  if (call.response.status !== 200 || call.parsed?.jsonrpc !== "2.0" || call.parsed?.id !== id || call.parsed?.error || !result || result.isError === true || (!textItems.length && !hasStructuredContent)) {
    // Do not log page/document contents: a generic excerpt is enough to diagnose this stage.
    fail(`tools/call:${name}`, call.response.status, "Tool call failed or returned no usable content.", call.response.headers.get("www-authenticate"), {
      jsonrpc: call.parsed?.jsonrpc ?? null,
      responseId: call.parsed?.id ?? null,
      expectedId: id,
      jsonRpcErrorPresent: !!call.parsed?.error,
      resultKeys: result && typeof result === "object" ? Object.keys(result) : [],
      contentItemTypes: Array.isArray(result?.content) ? result.content.map((item) => item?.type ?? "unknown") : [],
      resultIsError: result?.isError === true,
      hasUsableText: textItems.length > 0,
      hasStructuredContent: hasStructuredContent,
    });
  }
  return {
    name,
    httpStatus: call.response.status,
    isError: result.isError === true,
    contentItems: Array.isArray(result.content) ? result.content.length : 0,
    hasText: textItems.length > 0,
    structuredContentPresent: hasStructuredContent,
  };
}

try {
  const init = await request("initialize", 1, {
    protocolVersion: "2025-11-25",
    capabilities: {},
    clientInfo: { name: "chrono-cross-gpt-smoke-test", version: "1.0.0" },
  });
  if (init.response.status !== 200 || init.parsed?.jsonrpc !== "2.0" || init.parsed?.id !== 1 || init.parsed?.error || !init.parsed?.result?.serverInfo || init.parsed.result.serverInfo.name !== "chrono-cross-gpt") {
    fail("initialize", init.response.status, init.body, init.response.headers.get("www-authenticate"));
  }

  if (init.parsed.result.protocolVersion !== "2025-11-25") {
    fail("initialize", init.response.status, "Server negotiated an unsupported MCP protocol version.", init.response.headers.get("www-authenticate"));
  }

  const initialized = await request("notifications/initialized", undefined, undefined, init.parsed.result.protocolVersion);
  if (initialized.response.status !== 202 || initialized.body.trim().length !== 0) {
    fail("notifications/initialized", initialized.response.status, initialized.body, initialized.response.headers.get("www-authenticate"));
  }

  const listed = await request("tools/list", 2, undefined, init.parsed.result.protocolVersion);
  const tools = listed.parsed?.result?.tools;
  if (listed.response.status !== 200 || listed.parsed?.jsonrpc !== "2.0" || listed.parsed?.id !== 2 || listed.parsed?.error || !Array.isArray(tools)) {
    fail("tools/list", listed.response.status, listed.body, listed.response.headers.get("www-authenticate"));
  }
  const toolNames = tools.map((tool) => tool?.name).filter((name) => typeof name === "string");
  const expected = ["read_public_page", "get_browser_capabilities"];
  const missing = expected.filter((name) => !toolNames.includes(name));
  if (missing.length) {
    console.error(JSON.stringify({ ok: false, stage: "tools/list", reason: "expected_tools_missing", missing, toolNames, credentialPrinted: false }, null, 2));
    process.exit(1);
  }

  const capabilitiesCall = await callTool("get_browser_capabilities", 3, {}, init.parsed.result.protocolVersion);
  const publicPageCall = await callTool("read_public_page", 4, { url: "https://example.com/" }, init.parsed.result.protocolVersion);

  console.log(JSON.stringify({
    ok: true,
    endpoint: endpoint.origin + endpoint.pathname,
    initialize: { httpStatus: init.response.status, protocolVersion: init.parsed.result.protocolVersion, serverName: init.parsed.result.serverInfo.name },
    initializedNotification: { httpStatus: initialized.response.status, emptyBody: true },
    toolsList: { httpStatus: listed.response.status, toolNames },
    toolCalls: [capabilitiesCall, publicPageCall],
    credentialPrinted: false,
  }, null, 2));
} catch (error) {
  // Avoid printing arbitrary error objects or request details that might contain secrets.
  console.error(JSON.stringify({ ok: false, stage: "network_or_protocol", errorType: error instanceof Error ? error.name : "unknown", message: "Request failed. Check TLS/network access and the server response; no request headers or credentials were printed.", credentialPrinted: false }, null, 2));
  process.exit(1);
}
