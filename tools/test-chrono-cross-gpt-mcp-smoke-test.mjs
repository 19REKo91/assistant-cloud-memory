#!/usr/bin/env node
// Dependency-free local tests for chrono-cross-gpt-mcp-smoke-test.mjs.
// Dummy credentials only; a preloaded fetch mock intercepts every request.
// Run with: node tools/test-chrono-cross-gpt-mcp-smoke-test.mjs

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const script = resolve(here, "chrono-cross-gpt-mcp-smoke-test.mjs");
const dummyToken = "LOCAL-ONLY-dummy-token-000000000000000000000000000000";
const directory = mkdtempSync(join(tmpdir(), "chrono-mcp-smoke-"));
const preload = join(directory, "mock-fetch.mjs");

const mockSource = [
  "const expectedToken = process.env.CHRONO_MCP_TOKEN;",
  "const scenario = process.env.CHRONO_MCP_SMOKE_SCENARIO || 'success';",
  "const reject = (message) => { if (process.env.CHRONO_MCP_SMOKE_DEBUG === '1') console.error('MOCK_FETCH_REJECTED:', message); throw new Error(message); };"
  "globalThis.fetch = async (input, init = {}) => {",
  "  const url = new URL(String(input));",
  "  if (url.origin !== 'https://chrono-cross-gpt.floot.app' || url.pathname !== '/_api/mcp') reject('Unexpected destination in test mock');",
  "  if (init.redirect !== 'error') reject('Client must refuse redirects when sending credentials');",
  "  const request = JSON.parse(String(init.body));",
  "  const headers = new Headers(init.headers);",
  "  const authorization = headers.get('authorization');",
  "  const accept = headers.get('accept') || '';",
  "  if (!accept.includes('application/json') || !accept.includes('text/event-stream')) reject('Missing Streamable HTTP Accept values');",
  "  if (request.method !== 'initialize' && headers.get('mcp-protocol-version') !== '2025-11-25') reject('Missing negotiated MCP protocol version');",
  "  if (request.method === 'initialize' && headers.has('mcp-protocol-version')) reject('Initial request must not assume a negotiated version');",
  "  const reply = (payload, status = 200, forceJson = false) => {",
  "    if (!forceJson && scenario === 'sse' && payload !== null) return new Response('event: message\\ndata: ' + JSON.stringify(payload) + '\\n\\n', {status, headers:{'content-type':'text/event-stream'}});",
  "    return new Response(payload === null ? null : JSON.stringify(payload), {status, headers:{'content-type':'application/json'}});",
  "  };",
  "  if (scenario === 'unauthorized' && request.method === 'initialize' && authorization === 'Bearer ' + expectedToken) return new Response(JSON.stringify({jsonrpc:'2.0',id:request.id,error:{code:-32001,message:'authentication_required',echo:expectedToken}}), {status:401,headers:{'content-type':'application/json','www-authenticate':'Bearer realm=chrono-cross-gpt'}});",
  "  if (authorization !== 'Bearer ' + expectedToken) return new Response(JSON.stringify({error:'authentication_required'}), {status:401,headers:{'content-type':'application/json','www-authenticate':'Bearer realm=chrono-cross-gpt'}});",
  "  if (request.method === 'initialize') { const payload = {jsonrpc:'2.0',id:scenario === 'wrong_id' ? 999 : request.id,result:{protocolVersion:'2025-11-25',serverInfo:{name:scenario === 'wrong_server' ? 'unexpected-server' : 'chrono-cross-gpt',version:'0.2.0'},capabilities:{tools:{listChanged:false}}}}; return reply(payload); }",
  "  if (request.method === 'notifications/initialized') return new Response(null,{status:202});",
  "  if (request.method === 'tools/list') { const tools = scenario === 'missing_tool' ? [{name:'read_public_page'}] : [{name:'read_public_page'},{name:'get_browser_capabilities'}]; return reply({jsonrpc:'2.0',id:request.id,result:{tools}}); }",
  "  if (request.method === 'tools/call') {",
  "    const name = request.params?.name;",
  "    const args = request.params?.arguments || {};",
  "    if (name === 'get_browser_capabilities') return reply({jsonrpc:'2.0',id:request.id,result:{content:[{type:'text',text:'CHRONO CROSS GPT capability status: public page reading available.'}],structuredContent:{browserRuntime:false,remoteControl:false}}});",
  "    if (name === 'read_public_page') {",
  "      const raw = args.url;",
  "      let message = '';",
  "      if (typeof raw !== 'string' || raw.length > 2048) message = 'url must be a valid HTTP(S) URL string no longer than 2048 characters';",
  "      else { try { const parsed = new URL(raw); if (!['http:','https:'].includes(parsed.protocol)) message = 'Only HTTP and HTTPS addresses can be read'; else if (parsed.username || parsed.password) message = 'URLs containing embedded credentials are blocked'; else if (parsed.port && !((parsed.protocol === 'https:' && parsed.port === '443') || (parsed.protocol === 'http:' && parsed.port === '80'))) message = 'Non-standard ports are not supported'; else if (/^(127\\.|10\\.|192\\.168\\.|169\\.254\\.|0\\.|localhost$)/i.test(parsed.hostname) || parsed.hostname === '::1' || parsed.hostname === '127.1') message = 'Literal IP addresses are blocked'; } catch { message = 'url must be a valid HTTP(S) URL string no longer than 2048 characters'; } }",
  "      if (message) return reply({jsonrpc:'2.0',id:request.id,result:{isError:true,content:[{type:'text',text:message}]}});",
  "      if (raw !== 'https://example.com/') return reply({jsonrpc:'2.0',id:request.id,result:{isError:true,content:[{type:'text',text:'Mock only supports the Example Domain fixture'}]}});",
  "      return reply({jsonrpc:'2.0',id:request.id,result:{content:[{type:'text',text:'Example Domain\\nThis domain is for use in illustrative examples in documents.'}],structuredContent:{resultStatus:'returned',url:'https://example.com/',truncated:false}}});",
  "    }",
  "    return reply({jsonrpc:'2.0',id:request.id,error:{code:-32602,message:'Unknown tool'}});",
  "  }",
  "  return reply({jsonrpc:'2.0',id:request.id,error:{code:-32601,message:'unexpected method'}},400);",
  "};"
].join("\n");
writeFileSync(preload, mockSource);

function run(scenario, includeToken = true) {
  const env = { ...process.env, CHRONO_MCP_SMOKE_SCENARIO: scenario, CHRONO_MCP_SMOKE_DEBUG: "1" };
  env.CHRONO_MCP_TOKEN = includeToken ? dummyToken : "";
  return spawnSync(process.execPath, ["--import", preload, script], {
    encoding: "utf8",
    env,
    timeout: 10000,
  });
}

try {
  {
    const result = run("success");
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const output = JSON.parse(result.stdout);
    assert.equal(output.ok, true);
    assert.equal(output.initialize.serverName, "chrono-cross-gpt");
    assert.equal(output.initializedNotification.httpStatus, 202);
    assert.deepEqual(output.toolsList.toolNames, ["read_public_page", "get_browser_capabilities"]);
    assert.equal(output.toolCalls.getBrowserCapabilities.succeeded, true);
    assert.equal(output.toolCalls.readPublicPage.fixture, "https://example.com/");
    assert.equal(output.credentialPrinted, false);
    assert.ok(!result.stdout.includes(dummyToken));
    assert.ok(!result.stderr.includes(dummyToken));
    console.log("PASS success: initialize, tools/list, both tool calls, auth and URL security checks");
  }
  {
    const result = run("sse");
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const output = JSON.parse(result.stdout);
    assert.equal(output.ok, true);
    assert.equal(output.initialize.serverName, "chrono-cross-gpt");
    assert.deepEqual(output.toolsList.toolNames, ["read_public_page", "get_browser_capabilities"]);
    assert.equal(output.toolCalls.getBrowserCapabilities.succeeded, true);
    assert.equal(output.credentialPrinted, false);
    assert.ok(!result.stdout.includes(dummyToken));
    assert.ok(!result.stderr.includes(dummyToken));
    console.log("PASS SSE: parses Streamable HTTP event-stream responses");
  }
  {
    const result = run("unauthorized");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes('"stage": "initialize"'));
    assert.ok(combined.includes("[REDACTED]"));
    assert.ok(combined.includes('"wwwAuthenticate": "Bearer realm=chrono-cross-gpt"'));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS unauthorized: response body cannot leak a credential");
  }
  {
    const result = run("wrong_id");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.ok((result.stdout + result.stderr).includes("initialize"));
    console.log("PASS response ID validation");
  }
  {
    const result = run("wrong_server");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes('"stage": "initialize"'));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS server identity validation");
  }
  {
    const result = run("missing_tool");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes("expected_tools_missing"));
    assert.ok(combined.includes("get_browser_capabilities"));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS missing tool detection");
  }
  {
    const env = { ...process.env };
    delete env.CHRONO_MCP_TOKEN;
    delete env.CHRONO_MCP_SMOKE_SCENARIO;
    const result = spawnSync(process.execPath, [script], { encoding:"utf8", env, timeout:10000 });
    assert.equal(result.status, 2);
    assert.ok((result.stdout + result.stderr).includes("CHRONO_MCP_TOKEN is missing"));
    console.log("PASS missing credential: exits before network activity");
  }
  {
    const env = { ...process.env, CHRONO_MCP_TOKEN: "short", CHRONO_MCP_SMOKE_SCENARIO: "success" };
    const result = spawnSync(process.execPath, ["--import", preload, script], { encoding:"utf8", env, timeout:10000 });
    assert.equal(result.status, 2);
    assert.ok((result.stdout + result.stderr).includes("CHRONO_MCP_TOKEN is missing or malformed"));
    assert.ok(!(result.stdout + result.stderr).includes("LOCAL-ONLY"));
    console.log("PASS malformed credential: rejected before network activity");
  }
} finally {
  rmSync(directory, { recursive:true, force:true });
}
