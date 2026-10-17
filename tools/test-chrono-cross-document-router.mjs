#!/usr/bin/env node
// Offline end-to-end routing tests. Files are synthetic; no network is used.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readDocument, getDocumentReaderCapabilities } from "../chrono-reader-core/read-document.mjs";
const requireFromReaderPackage = createRequire(new URL("../chrono-reader-core/package.json", import.meta.url));
const { zipSync, strToU8 } = requireFromReaderPackage("fflate");

function archive(parts) {
  const mapped = {};
  for (const [name, value] of Object.entries(parts)) mapped[name] = strToU8(value);
  return Buffer.from(zipSync(mapped, { level: 0 }));
}
function makeDocx(text) {
  return archive({
    "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
    "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    "word/document.xml": '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'
  });
}
let passed = 0;
function pass(name) { passed += 1; console.log("PASS " + name); }
function failure(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.completeness, "unavailable");
  assert.equal(result.error.code, code);
  assert.equal(result.content, null);
}

{
  const result = await readDocument({ filename: "notes.txt", contentType: "text/plain", bytes: Buffer.from("مرحبا\nWorld", "utf8") });
  assert.equal(result.ok, true);
  assert.equal(result.method, "utf8-text-document-reader");
  assert.ok(result.content.text.includes("مرحبا"));
  pass("router selects UTF-8 text reader and preserves Arabic");
}
{
  const result = await readDocument({ filename: "data.csv", contentType: "text/csv", bytes: Buffer.from("Name,Count\nAlpha,2\n", "utf8") });
  assert.equal(result.ok, true);
  assert.equal(result.content.type, "table");
  assert.deepEqual(result.content.headers, ["Name", "Count"]);
  pass("router selects CSV parser and preserves columns");
}
{
  const marker = "CHRONO ROUTER DOCX";
  const result = await readDocument({
    filename: "report.docx",
    contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    bytes: makeDocx(marker)
  });
  assert.equal(result.ok, true, JSON.stringify(result.error));
  assert.ok(result.content.text.includes(marker));
  pass("router sends DOCX bytes through Office adapter");
}
{
  const result = await readDocument({ filename: "scan.pdf", contentType: "application/pdf", bytes: Buffer.from("%PDF-test") });
  failure(result, "provider_unavailable");
  assert.match(result.error.message, /published PDF endpoint/);
  pass("router does not misrepresent PDF route as implemented in this adapter");
}
{
  failure(await readDocument({ filename: "legacy.doc", bytes: Buffer.from("old doc") }), "unsupported_type");
  failure(await readDocument({ filename: "unknown.bin", bytes: Buffer.from("bytes") }), "unsupported_type");
  pass("unsupported file extensions fail with stable status");
}
{
  failure(await readDocument({ filename: "notes.txt", contentType: "text/plain" }), "malformed_input");
  failure(await readDocument(null), "malformed_input");
  pass("missing file bytes and invalid input shapes are handled");
}
{
  const capability = getDocumentReaderCapabilities();
  assert.equal(capability.routerStatus, "repository_only");
  const office = capability.readers.find((reader) => reader.id === "office.presentation");
  assert.deepEqual(office.extensions, [".pptx"]);
  assert.ok(capability.unavailableHere.includes("image OCR"));
  pass("capability report makes production integration and unavailable features explicit");
}
console.log(JSON.stringify({ ok: true, passedTests: passed, networkCalls: 0, sourceFiles: ["read-document.mjs", "read-text-document.mjs", "read-office-document.mjs"] }, null, 2));
