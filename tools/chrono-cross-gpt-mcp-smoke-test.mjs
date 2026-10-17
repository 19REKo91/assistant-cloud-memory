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

async function request(method, id, params, protocolVersion, authorizationToken = token) {
  const message = { jsonrpc: "2.0", method };
  if (id !== undefined) message.id = id;
  if (params !== undefined) message.params = params;
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
  };
  if (authorizationToken !== null) headers.Authorization = `Bearer ${authorizationToken}`;
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

async function callTool(name, id, args, protocolVersion, expectedText = null) {
  const call = await request("tools/call", id, { name, arguments: args }, protocolVersion);
  const result = call.parsed?.result;
  const textItems = Array.isArray(result?.content)
    ? result.content.filter((item) => item?.type === "text" && typeof item.text === "string" && item.text.trim().length > 0)
    : [];
  const hasStructuredContent = !!result?.structuredContent && typeof result.structuredContent === "object";
  const expectedTextFound = expectedText === null ? null : textItems.some((item) => item.text.includes(expectedText));
  if (call.response.status !== 200 || call.parsed?.jsonrpc !== "2.0" || call.parsed?.id !== id || call.parsed?.error || !result || result.isError === true || (!textItems.length && !hasStructuredContent) || (expectedText !== null && !expectedTextFound)) {
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
    expectedTextFound,
    structuredContentPresent: hasStructuredContent,
  };
}

async function callExpectedToolError(name, id, args, protocolVersion) {
  const call = await request("tools/call", id, { name, arguments: args }, protocolVersion);
  const result = call.parsed?.result;
  const rejected = !!call.parsed?.error || result?.isError === true;
  if (call.response.status !== 200 || call.parsed?.jsonrpc !== "2.0" || call.parsed?.id !== id || !rejected) {
    fail(`tools/call:${name}:unsafe-url`, call.response.status, "Disallowed URL was not rejected as a JSON-RPC/tool error.", call.response.headers.get("www-authenticate"), {
      jsonrpc: call.parsed?.jsonrpc ?? null,
      responseId: call.parsed?.id ?? null,
      jsonRpcErrorPresent: !!call.parsed?.error,
      resultIsError: result?.isError === true,
      resultKeys: result && typeof result === "object" ? Object.keys(result) : [],
    });
  }
  return { name, httpStatus: call.response.status, rejected: true };
}

try {
  const initParams = {
    protocolVersion: "2025-11-25",
    capabilities: {},
    clientInfo: { name: "chrono-cross-gpt-smoke-test", version: "1.0.0" },
  };
  const missingAuth = await request("initialize", 90, initParams, undefined, null);
  if (missingAuth.response.status !== 401 || missingAuth.body.includes(token)) {
    fail("missing_auth", missingAuth.response.status, "Missing-token request was not safely rejected.", missingAuth.response.headers.get("www-authenticate"));
  }
  const invalidToken = "CHRONO_CROSS_INVALID_TEST_TOKEN_000000000000";
  const wrongAuth = await request("initialize", 91, initParams, undefined, invalidToken);
  if (wrongAuth.response.status !== 401 || wrongAuth.body.includes(invalidToken) || wrongAuth.body.includes(token)) {
    fail("wrong_auth", wrongAuth.response.status, "Invalid-token request was not safely rejected without echoing credentials.", wrongAuth.response.headers.get("www-authenticate"));
  }

  const init = await request("initialize", 1, initParams);
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
  const readerTool = tools.find((tool) => tool?.name === "read_public_page");
  const readerSchema = readerTool?.inputSchema;
  if (readerSchema?.type !== "object" || readerSchema?.properties?.url?.type !== "string" || !Array.isArray(readerSchema.required) || !readerSchema.required.includes("url")) {
    fail("tools/list", listed.response.status, "read_public_page must declare a required string url input.", listed.response.headers.get("www-authenticate"));
  }

  const capabilitiesCall = await callTool("get_browser_capabilities", 3, {}, init.parsed.result.protocolVersion);
  const publicPageCall = await callTool("read_public_page", 4, { url: "https://example.com/" }, init.parsed.result.protocolVersion, "Example Domain");
  // file: is intentionally non-networked; this checks scheme rejection without probing private hosts.
  const unsafeUrlCall = await callExpectedToolError("read_public_page", 5, { url: "file:///etc/passwd" }, init.parsed.result.protocolVersion);

  console.log(JSON.stringify({
    ok: true,
    endpoint: endpoint.origin + endpoint.pathname,
    initialize: { httpStatus: init.response.status, protocolVersion: init.parsed.result.protocolVersion, serverName: init.parsed.result.serverInfo.name },
    initializedNotification: { httpStatus: initialized.response.status, emptyBody: true },
    authChecks: {
      missingToken: { httpStatus: missingAuth.response.status, rejected: true },
      wrongToken: { httpStatus: wrongAuth.response.status, rejected: true, tokenEchoed: false },
    },
    toolsList: { httpStatus: listed.response.status, toolNames, readPublicPageSchemaValid: true },
    toolCalls: [capabilitiesCall, publicPageCall],
    unsafeUrl: unsafeUrlCall,
    credentialPrinted: false,
  }, null, 2));
} catch (error) {
  // Avoid printing arbitrary error objects or request details that might contain secrets.
  console.error(JSON.stringify({ ok: false, stage: "network_or_protocol", errorType: error instanceof Error ? error.name : "unknown", message: "Request failed. Check TLS/network access and the server response; no request headers or credentials were printed.", credentialPrinted: false }, null, 2));
  process.exit(1);
}
