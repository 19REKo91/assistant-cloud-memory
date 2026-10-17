#!/usr/bin/env node
// Offline acceptance tests for the repository-side UTF-8/Markdown/CSV/JSON reader.
// No network calls, external dependencies, real user files, or secrets are used.
import assert from "node:assert/strict";
import { readTextDocument } from "../chrono-reader-core/read-text-document.mjs";

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log("PASS " + name);
}
function read(filename, text, contentType, limits) {
  return readTextDocument({
    filename,
    contentType,
    bytes: Buffer.isBuffer(text) ? text : Buffer.from(text, "utf8"),
    limits,
  });
}
function failure(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.error.code, code);
  assert.equal(result.completeness, "unavailable");
  assert.equal(result.content, null);
  assert.ok(!("stack" in result.error));
}

test("plain text preserves Unicode and produces line references", () => {
  const result = read("../../private/notes.txt", "مرحبا\nsecond line\n", "text/plain");
  assert.equal(result.ok, true);
  assert.equal(result.source.filename, "notes.txt");
  assert.equal(result.content.type, "text");
  assert.ok(result.content.text.includes("مرحبا"));
  assert.equal(result.content.lineCount, 3);
  assert.deepEqual(result.references[0], { kind: "line_range", startLine: 1, endLine: 3 });
});

test("Markdown preserves source and indexes headings with line numbers", () => {
  const result = read("guide.md", "# Main title\n\n### Detail ###\ntext", "text/markdown");
  assert.equal(result.ok, true);
  assert.equal(result.content.type, "markdown");
  assert.deepEqual(result.content.headings, [
    { level: 1, text: "Main title", line: 1 },
    { level: 3, text: "Detail", line: 3 },
  ]);
  assert.equal(result.references[1].line, 3);
});

test("CSV supports quoted commas, escaped quotes, CRLF and multiline fields", () => {
  const source = 'Name,Location,Note\r\nAda,"New York, NY","says ""hello"""\r\nGrace,London,"two\nlines"\r\n';
  const result = read("people.csv", source, "text/csv");
  assert.equal(result.ok, true);
  assert.equal(result.content.type, "table");
  assert.deepEqual(result.content.headers, ["Name", "Location", "Note"]);
  assert.deepEqual(result.content.rows[0], { rowNumber: 2, cells: ["Ada", "New York, NY", 'says "hello"'] });
  assert.deepEqual(result.content.rows[1], { rowNumber: 3, cells: ["Grace", "London", "two\nlines"] });
  assert.equal(result.content.rowCount, 2);
  assert.equal(result.warnings.length, 0);
});

test("CSV reports inconsistent-width rows without dropping cells", () => {
  const result = read("ragged.csv", "a,b\n1,2,3\n4\n", "text/csv");
  assert.equal(result.ok, true);
  assert.deepEqual(result.content.rows[0].cells, ["1", "2", "3"]);
  assert.equal(result.warnings.length, 2);
  assert.equal(result.warnings[0].code, "ragged_row");
});

test("CSV rejects an unterminated quote", () => {
  const result = read("bad.csv", 'name,value\nok,"unterminated', "text/csv");
  failure(result, "malformed_input");
});

test("CSV rejects a quote inside an unquoted field", () => {
  const result = read("bad.csv", 'name,value\nab"cd,1', "text/csv");
  failure(result, "malformed_input");
});

test("CSV enforces row limits including the header", () => {
  const result = read("too-many.csv", "a\n1\n2\n", "text/csv", { maxRows: 2 });
  failure(result, "size_limit_exceeded");
});

test("CSV enforces column and total-cell bounds", () => {
  failure(read("too-wide.csv", "a,b\n1,2", "text/csv", { maxColumns: 1 }), "size_limit_exceeded");
  failure(read("too-many-cells.csv", "a,b\n1,2", "text/csv", { maxCells: 3 }), "size_limit_exceeded");
});

test("JSON returns parsed structure and node count", () => {
  const result = read("data.json", '{"title":"test","values":[1,true,null]}', "application/json");
  assert.equal(result.ok, true);
  assert.equal(result.content.type, "json");
  assert.equal(result.content.value.title, "test");
  assert.equal(result.content.value.values[0], 1);
  assert.equal(result.content.nodeCount, 6);
});

test("JSON rejects malformed input without echoing the content", () => {
  const secretLikeText = '{"token":"DO-NOT-ECHO","broken":';
  const result = read("broken.json", secretLikeText, "application/json");
  failure(result, "malformed_input");
  assert.ok(!JSON.stringify(result).includes("DO-NOT-ECHO"));
});

test("JSON enforces nesting-depth and total-node limits", () => {
  failure(read("deep.json", '{"a":{"b":{"c":{"d":1}}}}', "application/json", { maxJsonDepth: 3 }), "size_limit_exceeded");
  failure(read("many.json", "[1,2,3,4]", "application/json", { maxJsonNodes: 3 }), "size_limit_exceeded");
});

test("empty uploads report empty_extraction", () => {
  failure(read("empty.txt", Buffer.alloc(0), "text/plain"), "empty_extraction");
  failure(read("spaces.md", "  \n\t", "text/markdown"), "empty_extraction");
});

test("invalid UTF-8 and NUL bytes are rejected", () => {
  failure(read("bad.txt", Buffer.from([0xc3, 0x28]), "text/plain"), "malformed_input");
  failure(read("binary.txt", Buffer.from([0x41, 0x00, 0x42]), "text/plain"), "malformed_input");
});

test("file-size limits are enforced before decoding", () => {
  failure(read("large.txt", "four", "text/plain", { maxBytes: 3 }), "size_limit_exceeded");
});

test("oversized typed-array inputs are rejected before buffer copying", () => {
  const bytes = new Uint8Array(4096);
  const result = readTextDocument({ filename: "large.txt", contentType: "text/plain", bytes, limits: { maxBytes: 32 } });
  failure(result, "size_limit_exceeded");
  assert.equal(result.source.byteSize, 4096);
});

test("unsupported extension and MIME mismatch are rejected", () => {
  failure(read("doc.docx", "not a word document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), "unsupported_type");
  failure(read("notes.txt", "hello", "application/pdf"), "unsupported_type");
});

test("invalid input shapes do not throw", () => {
  const result = readTextDocument(null);
  failure(result, "malformed_input");
  failure(readTextDocument({ filename: "missing.txt", contentType: "text/plain" }), "malformed_input");
});

console.log(JSON.stringify({ ok: true, passedTests: passed, networkCalls: 0, externalDependencies: 0 }, null, 2));
