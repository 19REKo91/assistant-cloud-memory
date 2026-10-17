#!/usr/bin/env node
// Offline fixtures for the Office/EPUB reader. No network calls or user files.
import assert from "node:assert/strict";
import { zipSync, strToU8 } from "fflate";
import { readOfficeDocument } from "../chrono-reader-core/read-office-document.mjs";

let passed = 0;
function pass(name) {
  passed += 1;
  console.log("PASS " + name);
}
function failure(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.completeness, "unavailable");
  assert.equal(result.error.code, code);
  assert.equal(result.content, null);
  assert.ok(!("stack" in result.error));
}
function archive(parts) {
  const mapped = {};
  for (const [name, value] of Object.entries(parts)) mapped[name] = strToU8(value);
  return Buffer.from(zipSync(mapped, { level: 0 }));
}
function makeDocx(text) {
  return archive({
    "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
    "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    "word/document.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'
  });
}
function makeXlsx() {
  return archive({
    "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
    "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
    "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="SmokeData" sheetId="1" r:id="rId1"/></sheets></workbook>',
    "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
    "xl/worksheets/sheet1.xml": '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Product</t></is></c><c r="B1" t="inlineStr"><is><t>Count</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>CHRONO OFFICE SHEET</t></is></c><c r="B2" t="n"><v>7</v></c></row></sheetData></worksheet>'
  });
}

const docxText = "CHRONO DOCX FIXTURE";
const docx = makeDocx(docxText);
const docxResult = await readOfficeDocument({
  filename: "quarterly-report.docx",
  contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  bytes: docx
});
assert.equal(docxResult.ok, true, JSON.stringify(docxResult.error));
assert.equal(docxResult.source.filename, "quarterly-report.docx");
assert.equal(docxResult.method, "officeparser");
assert.ok(docxResult.content.text.includes(docxText), "DOCX marker missing");
assert.ok(["complete", "partial"].includes(docxResult.completeness));
pass("DOCX: reads synthetic paragraph text from an in-memory Office package");

const xlsx = makeXlsx();
const xlsxResult = await readOfficeDocument({
  filename: "metrics.xlsx",
  contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  bytes: xlsx
});
assert.equal(xlsxResult.ok, true, JSON.stringify(xlsxResult.error));
assert.ok(xlsxResult.content.text.includes("Product"), "XLSX header missing");
assert.ok(xlsxResult.content.text.includes("CHRONO OFFICE SHEET"), "XLSX cell text missing");
assert.ok(xlsxResult.content.text.includes("7"), "XLSX numeric value missing");
assert.ok(["complete", "partial"].includes(xlsxResult.completeness));
pass("XLSX: reads a synthetic worksheet including header and cell values");

{
  const result = await readOfficeDocument({ filename: "bad.docx", contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", bytes: Buffer.from("this is not a zip archive") });
  failure(result, "malformed_input");
  pass("malformed Office package fails with a safe typed error");
}
{
  const result = await readOfficeDocument({ filename: "book.docx", contentType: "text/plain", bytes: docx });
  failure(result, "unsupported_type");
  pass("MIME/extension mismatch is rejected");
}
{
  const result = await readOfficeDocument({ filename: "old.doc", contentType: "application/msword", bytes: Buffer.from("legacy Word") });
  failure(result, "unsupported_type");
  pass("legacy .doc is not mistaken for DOCX support");
}
{
  const result = await readOfficeDocument({ filename: "archive.zip", bytes: docx });
  failure(result, "unsupported_type");
  pass("arbitrary ZIP archives are not accepted");
}
{
  const result = await readOfficeDocument({ filename: "empty.docx", bytes: Buffer.alloc(0) });
  failure(result, "empty_extraction");
  pass("empty Office upload is rejected");
}
{
  const result = await readOfficeDocument({ filename: "too-large.docx", bytes: Buffer.alloc(4 * 1024 * 1024 + 1) });
  failure(result, "size_limit_exceeded");
  assert.equal(result.source.byteSize, 4 * 1024 * 1024 + 1);
  pass("input byte limit is checked before the Office parser runs");
}
{
  const result = await readOfficeDocument({ filename: "report.docx", bytes: docx, limits: { maxOutputChars: 8 } });
  assert.equal(result.ok, true);
  assert.equal(result.completeness, "partial");
  assert.equal(result.content.truncated, true);
  assert.equal(result.content.text.length, 8);
  assert.ok(result.warnings.some((warning) => warning.code === "OUTPUT_TRUNCATED"));
  pass("output cap returns a labelled partial result");
}
{
  const result = await readOfficeDocument(null);
  failure(result, "malformed_input");
  pass("invalid top-level input returns a typed error rather than throwing");
}

console.log(JSON.stringify({
  ok: true,
  passedTests: passed,
  fixtureTypes: ["DOCX", "XLSX"],
  networkCalls: 0,
  originalDocumentContentPrinted: false,
  defaultInputLimitBytes: 4 * 1024 * 1024
}, null, 2));
