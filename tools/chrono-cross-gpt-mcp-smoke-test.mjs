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

function fail(stage, status, body, challenge) {
  console.error(JSON.stringify({
    ok: false,
    stage,
    httpStatus: status,
    wwwAuthenticate: challenge || null,
    responseExcerpt: (body || "").slice(0, 350) || null,
    credentialPrinted: false,
  }, null, 2));
  process.exit(1);
}

try {
  const init = await request("initialize", 1, {
    protocolVersion: "2025-11-25",
    capabilities: {},
    clientInfo: { name: "chrono-cross-gpt-smoke-test", version: "1.0.0" },
  });
  if (init.response.status !== 200 || init.parsed?.id !== 1 || !init.parsed?.result?.serverInfo || init.parsed.result.serverInfo.name !== "chrono-cross-gpt") {
    fail("initialize", init.response.status, init.body, init.response.headers.get("www-authenticate"));
  }

  const initialized = await request("notifications/initialized", undefined, undefined, init.parsed.result.protocolVersion);
  if (initialized.response.status !== 202 || initialized.body.length !== 0) {
    fail("notifications/initialized", initialized.response.status, initialized.body, initialized.response.headers.get("www-authenticate"));
  }

  const listed = await request("tools/list", 2, undefined, init.parsed.result.protocolVersion);
  const tools = listed.parsed?.result?.tools;
  if (listed.response.status !== 200 || listed.parsed?.id !== 2 || !Array.isArray(tools)) {
    fail("tools/list", listed.response.status, listed.body, listed.response.headers.get("www-authenticate"));
  }
  const toolNames = tools.map((tool) => tool?.name).filter((name) => typeof name === "string");
  const expected = ["read_public_page", "get_browser_capabilities"];
  const missing = expected.filter((name) => !toolNames.includes(name));
  if (missing.length) {
    console.error(JSON.stringify({ ok: false, stage: "tools/list", reason: "expected_tools_missing", missing, toolNames, credentialPrinted: false }, null, 2));
    process.exit(1);
  }

  console.log(JSON.stringify({
    ok: true,
    endpoint: endpoint.origin + endpoint.pathname,
    initialize: { httpStatus: init.response.status, protocolVersion: init.parsed.result.protocolVersion, serverName: init.parsed.result.serverInfo.name },
    initializedNotification: { httpStatus: initialized.response.status, emptyBody: true },
    toolsList: { httpStatus: listed.response.status, toolNames },
    credentialPrinted: false,
  }, null, 2));
} catch (error) {
  // Avoid printing arbitrary error objects or request details that might contain secrets.
  console.error(JSON.stringify({ ok: false, stage: "network_or_protocol", errorType: error instanceof Error ? error.name : "unknown", message: "Request failed. Check TLS/network access and the server response; no request headers or credentials were printed.", credentialPrinted: false }, null, 2));
  process.exit(1);
}
