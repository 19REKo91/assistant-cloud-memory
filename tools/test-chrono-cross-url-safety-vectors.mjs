#!/usr/bin/env node
// Offline integrity checks for URL-safety test vectors.
// This validates the test data only; it does not exercise the live reader or make network requests.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const file = resolve(here, "../docs/CHRONO_CROSS_URL_SAFETY_TEST_VECTORS.json");
const data = JSON.parse(readFileSync(file, "utf8"));

assert.equal(data.schemaVersion, 1, "unexpected vector schema version");
assert.match(data.purpose, /do not prove/i, "purpose must state this is not proof of runtime enforcement");
assert.ok(Array.isArray(data.cases) && data.cases.length >= 20, "expected broad security coverage");
assert.ok(Array.isArray(data.executionNotes) && data.executionNotes.length >= 3, "missing safe execution guidance");

const ids = new Set();
for (const test of data.cases) {
  assert.equal(typeof test.id, "string", "every case needs an id");
  assert.ok(test.id.length > 0, "case id must not be empty");
  assert.ok(!ids.has(test.id), `duplicate case id: ${test.id}`);
  ids.add(test.id);
  assert.equal(typeof test.url, "string", `${test.id}: URL must be a string`);
  assert.equal(typeof test.expected, "string", `${test.id}: expected outcome is required`);
  assert.equal(typeof test.reason, "string", `${test.id}: rationale is required`);
  assert.ok(test.expected.length > 0 && test.reason.length > 0, `${test.id}: outcome/rationale must not be empty`);
  if (!test.id.includes("malformed")) {
    assert.doesNotThrow(() => new URL(test.url), `${test.id}: expected URL parser should accept the test fixture string`);
  }
}

// Confirm the JavaScript URL parser canonicalizes legacy numeric IPv4 forms before any
// destination allow/deny decision. This tests parser behavior, not the app's network layer.
for (const raw of [
  "http://2130706433/",
  "http://0x7f000001/",
  "http://127.1/",
]) {
  assert.equal(new URL(raw).hostname, "127.0.0.1", `legacy loopback encoding not canonicalized: ${raw}`);
}
assert.equal(new URL("http://[::ffff:127.0.0.1]/").hostname, "[::ffff:7f00:1]",
  "IPv4-mapped IPv6 fixture must be normalized by the runtime URL parser");

const byId = new Map(data.cases.map((test) => [test.id, test]));
for (const required of [
  "block-file-scheme",
  "block-localhost",
  "block-ipv4-link-local",
  "block-ipv6-loopback",
  "block-private-dns-resolution",
  "block-redirect-to-private",
  "block-redirect-to-metadata",
  "block-redirect-loop",
  "block-dns-rebinding",
  "strip-credentials-on-cross-origin-redirect",
  "block-malformed-url",
]) {
  assert.ok(byId.has(required), `missing required security vector: ${required}`);
}

assert.ok(data.policy.maxRedirects > 0 && data.policy.maxRedirects <= 10, "redirect limit must be bounded");
assert.equal(data.policy.revalidateEveryRedirectTarget, true, "every redirect target must be revalidated");
assert.equal(data.policy.neverForwardAuthorizationCookiesOrUserSecretsToRedirectTargets, true, "redirect credential policy must be explicit");

console.log(`PASS URL safety vector integrity: ${data.cases.length} cases, unique IDs, required attack classes, bounded redirect policy.`);
console.log("NOTE: this checks fixture integrity only; the application reader itself was not tested.");
