#!/usr/bin/env node
// Dependency-free local tests for chrono-cross-gpt-mcp-smoke-test.mjs.
// All credentials in this test are dummy values. The preloaded fetch mock
// intercepts every network request; these tests never contact production.
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
  "globalThis.fetch = async (input, init = {}) => {",
  "  const url = new URL(String(input));",
  "  if (url.origin !== 'https://chrono-cross-gpt.floot.app' || url.pathname !== '/_api/mcp') throw new Error('Unexpected destination in test mock');",
  "  if (init.redirect !== 'error') throw new Error('Client must refuse redirects when sending credentials');",
  "  const request = JSON.parse(String(init.body));",
  "  const requestHeaders = new Headers(init.headers);",
  "  const authorization = requestHeaders.get('authorization');",
  "  const accept = requestHeaders.get('accept') || '';",
  "  if (!accept.includes('application/json') || !accept.includes('text/event-stream')) throw new Error('Missing Streamable HTTP Accept values');",
  "  if (request.method !== 'initialize' && requestHeaders.get('mcp-protocol-version') !== '2025-11-25') throw new Error('Missing negotiated MCP protocol version');",
  "  if (request.method === 'initialize' && requestHeaders.has('mcp-protocol-version')) throw new Error('Initial request must not assume a negotiated version');",
  "  if (authorization !== 'Bearer ' + expectedToken) throw new Error('Dummy token was not sent in the expected header');",
  "  if (scenario === 'unauthorized' && request.method === 'initialize') return new Response(JSON.stringify({error:'authentication_required', echoed:expectedToken}), {status:401,headers:{'content-type':'application/json','www-authenticate':'Bearer realm=chrono-cross-gpt'}});",
  "  if (request.method === 'initialize') { const payload = JSON.stringify({jsonrpc:'2.0',id:scenario === 'wrong_id' ? 999 : request.id,result:{protocolVersion:'2025-11-25',serverInfo:{name:scenario === 'wrong_server' ? 'unexpected-server' : 'chrono-cross-gpt',version:'0.2.0'},capabilities:{tools:{listChanged:false}}}}); if (scenario === 'sse') return new Response('event: message\\ndata: ' + payload + '\\n\\n',{status:200,headers:{'content-type':'text/event-stream'}}); return new Response(payload,{status:200,headers:{'content-type':'application/json'}}); }",
  "  if (request.method === 'notifications/initialized') return new Response(null,{status:202});",
  "  if (request.method === 'tools/list') { const tools = scenario === 'missing_tool' ? [{name:'read_public_page'}] : [{name:'read_public_page'},{name:'get_browser_capabilities'}]; const payload = JSON.stringify({jsonrpc:'2.0',id:request.id,result:{tools}}); if (scenario === 'sse') return new Response('event: message\\ndata: ' + payload + '\\n\\n',{status:200,headers:{'content-type':'text/event-stream'}}); return new Response(payload,{status:200,headers:{'content-type':'application/json'}}); }",
  "  if (request.method === 'tools/call') { const name = request.params?.name; const failed = scenario === 'tool_error' && name === 'read_public_page'; const payload = JSON.stringify({jsonrpc:'2.0',id:request.id,result:failed ? {isError:true,content:[{type:'text',text:'mock failure'}]} : {content:[{type:'text',text:name === 'get_browser_capabilities' ? '{\"capabilities\":[\"public_page_text\"]}' : 'Example Domain'}]}}); if (scenario === 'sse') return new Response('event: message\\ndata: ' + payload + '\\n\\n',{status:200,headers:{'content-type':'text/event-stream'}}); return new Response(payload,{status:200,headers:{'content-type':'application/json'}}); }",
  "  return new Response('unexpected method',{status:400});",
  "};"
].join("\n");
writeFileSync(preload, mockSource);

function run(scenario, includeToken = true) {
  const env = { ...process.env, CHRONO_MCP_SMOKE_SCENARIO: scenario };
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
    assert.deepEqual(output.toolCalls.map((call) => call.name), ["get_browser_capabilities", "read_public_page"]);
    assert.ok(output.toolCalls.every((call) => call.httpStatus === 200 && call.hasText));
    assert.equal(output.credentialPrinted, false);
    assert.ok(!result.stdout.includes(dummyToken));
    assert.ok(!result.stderr.includes(dummyToken));
    console.log("PASS success: full protocol sequence and both tools");
  }
  {
    const result = run("sse");
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const output = JSON.parse(result.stdout);
    assert.equal(output.ok, true);
    assert.equal(output.initialize.serverName, "chrono-cross-gpt");
    assert.deepEqual(output.toolsList.toolNames, ["read_public_page", "get_browser_capabilities"]);
    assert.deepEqual(output.toolCalls.map((call) => call.name), ["get_browser_capabilities", "read_public_page"]);
    assert.equal(output.credentialPrinted, false);
    assert.ok(!result.stdout.includes(dummyToken));
    assert.ok(!result.stderr.includes(dummyToken));
    console.log("PASS SSE: parses Streamable HTTP event-stream responses for initialize and tools/list");
  }
  {
    const result = run("tool_error");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes('"stage": "tools/call:read_public_page"'));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS tool-call failure: detects reader errors without exposing credentials");
  }
  {
    const result = run("unauthorized");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes('"stage": "initialize"'));
    assert.ok(combined.includes("[REDACTED]"));
    assert.ok(combined.includes('"wwwAuthenticate": "Bearer realm=chrono-cross-gpt"'));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS unauthorized: reports 401 challenge without echoing the dummy credential");
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
    console.log("PASS server identity: rejects an unexpected MCP server identity");
  }
  {
    const result = run("missing_tool");
    assert.equal(result.status, 1, result.stdout + result.stderr);
    const combined = result.stdout + result.stderr;
    assert.ok(combined.includes("expected_tools_missing"));
    assert.ok(combined.includes("get_browser_capabilities"));
    assert.ok(!combined.includes(dummyToken));
    console.log("PASS missing tool: detects incomplete tool list");
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
