#!/usr/bin/env node
// Dependency-free validation for the evidence-based CHRONO CROSS GPT capability registry.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const path = new URL("../docs/CHRONO_CROSS_CAPABILITY_STATUS.json", import.meta.url);
const registry = JSON.parse(readFileSync(path, "utf8"));
const allowed = new Set(registry.statusVocabulary);
const requiredIds = [
  "mcp.protocol",
  "mcp.tool_calls",
  "files.text_markdown_csv_json",
  "files.office_document_adapter",
  "files.unified_reader_router",
  "bridge.reader_api",
  "infra.free_render_blueprint",
  "web.public_page_text",
  "web.file_scheme_rejection",
  "web.ssrf_redirect_dns",
  "pdf.selectable_text",
  "pdf.malformed_rejection",
  "pdf.unsupported_type",
  "pdf.scanned_ocr",
  "office.readers",
  "image.ocr",
  "audio.transcription",
  "video.transcription",
  "browser.javascript_rendering",
  "browser.dom_automation",
  "workspace.local_persistence",
  "workspace.server_persistence",
  "client.compatible_mcp",
  "client.chatgpt_android_mcp",
];

assert.equal(registry.schemaVersion, 1, "Unsupported registry schema version");
assert.ok(Array.isArray(registry.capabilities) && registry.capabilities.length > 0, "Capability list is empty");
const ids = registry.capabilities.map((capability) => capability.id);
assert.equal(new Set(ids).size, ids.length, "Capability IDs must be unique");
for (const id of requiredIds) assert.ok(ids.includes(id), `Missing required capability: ${id}`);

const byId = new Map(registry.capabilities.map((capability) => [capability.id, capability]));
const statusCounts = Object.fromEntries([...allowed].map((status) => [status, 0]));
for (const capability of registry.capabilities) {
  assert.ok(typeof capability.id === "string" && capability.id.trim(), "Capability ID is required");
  assert.ok(typeof capability.name === "string" && capability.name.trim(), `${capability.id}: name is required`);
  assert.ok(allowed.has(capability.status), `${capability.id}: invalid status ${capability.status}`);
  assert.ok(Array.isArray(capability.inputs), `${capability.id}: inputs must be an array`);
  assert.ok(Array.isArray(capability.outputs), `${capability.id}: outputs must be an array`);
  assert.ok(Array.isArray(capability.evidence), `${capability.id}: evidence must be an array`);
  assert.ok(Array.isArray(capability.limitations), `${capability.id}: limitations must be an array`);
  statusCounts[capability.status] += 1;

  if (capability.status === "implemented_and_tested") {
    assert.ok(capability.evidence.length > 0, `${capability.id}: tested capability requires evidence`);
  }
  if (capability.status === "blocked_unavailable") {
    assert.ok(typeof capability.blocker === "string" && capability.blocker.trim(), `${capability.id}: blocked capability requires a blocker`);
  }
  if (["implemented_unverified", "partial", "planned", "blocked_unavailable"].includes(capability.status)) {
    assert.ok(capability.limitations.length > 0, `${capability.id}: limitations must explain current scope`);
  }
  for (const evidence of capability.evidence) {
    assert.ok(typeof evidence.label === "string" && evidence.label.trim(), `${capability.id}: evidence label required`);
    const url = new URL(evidence.url);
    assert.equal(url.protocol, "https:", `${capability.id}: evidence URL must use HTTPS`);
    assert.ok(typeof evidence.verifiedAt === "string" && /^20\d\d-\d\d-\d\d$/.test(evidence.verifiedAt), `${capability.id}: evidence date must be ISO YYYY-MM-DD`);
  }
}
assert.ok(byId.get("client.chatgpt_android_mcp").status === "blocked_unavailable", "Do not claim direct Android MCP support");
assert.ok(byId.get("workspace.local_persistence").status !== "implemented_and_tested", "Unverified Floot persistence must not be reported as tested");
const serialized = JSON.stringify(registry);
assert.ok(!/Bearer\s+[A-Za-z0-9._-]{20,}/i.test(serialized), "Registry must not contain bearer credentials");
assert.ok(!/CHRONO_MCP_TOKEN\s*[:=]\s*[^\s"]{12,}/i.test(serialized), "Registry must not contain secret values");

console.log(JSON.stringify({
  ok: true,
  capabilityCount: registry.capabilities.length,
  statusCounts,
  testedCapabilitiesRequireEvidence: true,
  secretScan: "passed",
}, null, 2));
