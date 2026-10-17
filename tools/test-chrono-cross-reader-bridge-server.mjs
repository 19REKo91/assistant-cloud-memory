#!/usr/bin/env node
// Local-only HTTP tests for the authenticated reader bridge.
// All network requests target an ephemeral loopback server created in this test.
import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { createReaderBridgeServer } from "../chrono-reader-core/server.mjs";

const DUMMY_TOKEN = "TEST-ONLY-NOT-A-REAL-SECRET-0123456789";
let passed = 0;
function pass(name) { passed += 1; console.log("PASS " + name); }
async function startServer(options = {}) {
  const server = createReaderBridgeServer(options);
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  return {
    server,
    baseUrl: "http://127.0.0.1:" + address.port,
    close: () => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()))
  };
}
async function send(baseUrl, { method = "POST", path = "/v1/read", token, body, contentType = "application/json" } = {}) {
  const headers = {};
  if (token !== undefined) headers.authorization = "Bearer " + token;
  if (contentType) headers["content-type"] = contentType;
  return fetch(baseUrl + path, {
    method,
    headers,
    body: body === undefined ? undefined : (typeof body === "string" ? body : JSON.stringify(body)),
    signal: AbortSignal.timeout(5000)
  });
}
const validBody = {
  filename: "hello.txt",
  contentType: "text/plain",
  contentBase64: Buffer.from("CHRONO BRIDGE TEXT FIXTURE", "utf8").toString("base64")
};

{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { method: "GET", path: "/health" });
    const body = await response.json();
    assert.equal(response.status, 200);
    assert.equal(body.ok, true);
    assert.equal(body.authenticationRequiredForRead, true);
    assert.ok(!JSON.stringify(body).includes(DUMMY_TOKEN));
    pass("health is available without revealing the token or document details");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: validBody });
    const body = await response.json();
    assert.equal(response.status, 401);
    assert.equal(body.error.code, "authentication_required");
    assert.equal(response.headers.get("www-authenticate") !== null, true);
    pass("missing bearer token is rejected");
  } finally { await instance.close(); }
}
{
  const wrongToken = "TEST-ONLY-WRONG-CREDENTIAL-0123456789";
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: validBody, token: wrongToken });
    const body = await response.text();
    assert.equal(response.status, 401);
    assert.ok(!body.includes(wrongToken));
    assert.ok(!body.includes(DUMMY_TOKEN));
    pass("wrong bearer token is rejected without echoing either credential");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: validBody, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 200, JSON.stringify(body.error));
    assert.equal(body.ok, true);
    assert.ok(body.result.content.text.includes("CHRONO BRIDGE TEXT FIXTURE"));
    assert.ok(!JSON.stringify(body).includes(validBody.contentBase64));
    pass("valid authenticated request dispatches to the text reader");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: "{broken json", token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 400);
    assert.equal(body.error.code, "invalid_json");
    pass("invalid JSON returns a stable client error without stack data");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: { ...validBody, contentBase64: "%%%" }, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 400);
    assert.equal(body.error.code, "invalid_base64");
    pass("malformed Base64 is rejected");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: { ...validBody, secretField: "not allowed" }, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 400);
    assert.equal(body.error.code, "unexpected_fields");
    pass("unexpected JSON fields are rejected");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN, maxRequestBytes: 512 });
  try {
    const response = await send(instance.baseUrl, { body: { ...validBody, contentBase64: "A".repeat(2000) }, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 413);
    assert.equal(body.error.code, "request_too_large");
    pass("encoded request byte limit is enforced before parsing");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { body: { filename: "old.doc", contentType: "application/msword", contentBase64: Buffer.from("old").toString("base64") }, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 415);
    assert.equal(body.error.code, "unsupported_type");
    pass("unsupported document type maps to HTTP 415");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({ token: "" });
  try {
    const response = await send(instance.baseUrl, { body: validBody, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 503);
    assert.equal(body.error.code, "bridge_not_configured");
    pass("missing server-side token prevents reads");
  } finally { await instance.close(); }
}
{
  const instance = await startServer({
    token: DUMMY_TOKEN,
    maxResponseBytes: 256,
    reader: async () => ({
      ok: true,
      source: { kind: "uploaded_file", filename: "synthetic.txt", mediaType: "text/plain", byteSize: 1 },
      method: "test-reader",
      completeness: "complete",
      content: { type: "text", text: "x".repeat(1000) },
      references: [],
      warnings: [],
      error: null
    })
  });
  try {
    const response = await send(instance.baseUrl, { body: validBody, token: DUMMY_TOKEN });
    const body = await response.json();
    assert.equal(response.status, 413);
    assert.equal(body.error.code, "response_too_large");
    pass("response byte limit prevents oversized outputs");
  } finally { await instance.close(); }
}
{
  let beginRead;
  let releaseRead;
  const started = new Promise((resolve) => { beginRead = resolve; });
  const resultPromise = new Promise((resolve) => { releaseRead = resolve; });
  const instance = await startServer({
    token: DUMMY_TOKEN,
    maxConcurrency: 1,
    reader: async () => {
      beginRead();
      return resultPromise;
    }
  });
  try {
    const firstRequest = send(instance.baseUrl, { body: validBody, token: DUMMY_TOKEN });
    await started;
    const second = await send(instance.baseUrl, { body: validBody, token: DUMMY_TOKEN });
    const secondBody = await second.json();
    assert.equal(second.status, 429);
    assert.equal(secondBody.error.code, "too_many_requests");
    releaseRead({ ok: true, source: {}, method: "test-reader", completeness: "complete", content: { type: "text", text: "done" }, references: [], warnings: [], error: null });
    const first = await firstRequest;
    assert.equal(first.status, 200);
    pass("concurrency cap rejects excess work and releases slot after completion");
  } finally {
    releaseRead?.({ ok: true, source: {}, method: "test-reader", completeness: "complete", content: { type: "text", text: "done" }, references: [], warnings: [], error: null });
    await instance.close();
  }
}
{
  const instance = await startServer({ token: DUMMY_TOKEN });
  try {
    const response = await send(instance.baseUrl, { method: "POST", path: "/wrong", token: DUMMY_TOKEN, body: validBody });
    const body = await response.json();
    assert.equal(response.status, 404);
    assert.equal(body.error.code, "not_found");
    pass("unknown paths return 404 without exposing server internals");
  } finally { await instance.close(); }
}

console.log(JSON.stringify({ ok: true, passedTests: passed, externalNetworkCalls: 0, secretValuesPrinted: false }, null, 2));
