#!/usr/bin/env node
// Offline fixtures for the Office/EPUB reader. No network calls or user files.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readOfficeDocument } from "../chrono-reader-core/read-office-document.mjs";
const requireFromReaderPackage = createRequire(new URL("../chrono-reader-core/package.json", import.meta.url));
const { zipSync, strToU8 } = requireFromReaderPackage("fflate");

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

function makePptx(text) {
  return archive({
    "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>',
    "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>',
    "ppt/presentation.xml": '<?xml version="1.0" encoding="UTF-8"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst><p:sldSz cx="9144000" cy="5143500"/></p:presentation>',
    "ppt/_rels/presentation.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>',
    "ppt/slides/slide1.xml": '<?xml version="1.0" encoding="UTF-8"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:sp><p:nvSpPr><p:cNvPr id="2" name="TextBox 1"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"/><a:t>' + text + '</a:t></a:r><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
  });
}

function makeOdt(text) {
  return archive({
    "mimetype": "application/vnd.oasis.opendocument.text",
    "content.xml": '<?xml version="1.0" encoding="UTF-8"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2"><office:body><office:text><text:p>' + text + '</text:p></office:text></office:body></office:document-content>'
  });
}
function makeOds() {
  return archive({
    "mimetype": "application/vnd.oasis.opendocument.spreadsheet",
    "content.xml": '<?xml version="1.0" encoding="UTF-8"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2"><office:body><office:spreadsheet><table:table table:name="SmokeData"><table:table-row><table:table-cell office:value-type="string"><text:p>Product</text:p></table:table-cell><table:table-cell office:value-type="string"><text:p>Count</text:p></table:table-cell></table:table-row><table:table-row><table:table-cell office:value-type="string"><text:p>CHRONO ODS FIXTURE</text:p></table:table-cell><table:table-cell office:value-type="float" office:value="9"><text:p>9</text:p></table:table-cell></table:table-row></table:table></office:spreadsheet></office:body></office:document-content>'
  });
}
function makeOdp(text) {
  return archive({
    "mimetype": "application/vnd.oasis.opendocument.presentation",
    "content.xml": '<?xml version="1.0" encoding="UTF-8"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2"><office:body><office:presentation><draw:page draw:name="Slide1" draw:style-name="dp1"><draw:frame draw:style-name="gr1"><draw:text-box><text:p>' + text + '</text:p></draw:text-box></draw:frame></draw:page></office:presentation></office:body></office:document-content>'
  });
}
function makeEpub(text) {
  return archive({
    "mimetype": "application/epub+zip",
    "META-INF/container.xml": '<?xml version="1.0" encoding="UTF-8"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
    "OEBPS/content.opf": '<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">urn:uuid:chrono-smoke</dc:identifier><dc:title>Smoke Book</dc:title><dc:language>en</dc:language></metadata><manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="chapter"/></spine></package>',
    "OEBPS/chapter.xhtml": '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>Smoke</title></head><body><h1>' + text + '</h1></body></html>'
  });
}

const pptxText = "CHRONO PPTX SLIDE FIXTURE";
const pptxResult = await readOfficeDocument({
  filename: "deck.pptx",
  contentType: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  bytes: makePptx(pptxText)
});
assert.equal(pptxResult.ok, true, JSON.stringify(pptxResult.error));
assert.ok(pptxResult.content.text.includes(pptxText), "PPTX slide marker missing");
pass("PPTX: extracts text from a synthetic presentation slide");

for (const [extension, mediaType, bytes, marker] of [
  [".odt", "application/vnd.oasis.opendocument.text", makeOdt("CHRONO ODT FIXTURE"), "CHRONO ODT FIXTURE"],
  [".ods", "application/vnd.oasis.opendocument.spreadsheet", makeOds(), "CHRONO ODS FIXTURE"],
  [".odp", "application/vnd.oasis.opendocument.presentation", makeOdp("CHRONO ODP FIXTURE"), "CHRONO ODP FIXTURE"],
  [".epub", "application/epub+zip", makeEpub("CHRONO EPUB FIXTURE"), "CHRONO EPUB FIXTURE"]
]) {
  const result = await readOfficeDocument({
    filename: "document" + extension,
    contentType: mediaType,
    bytes
  });
  assert.equal(result.ok, true, extension + ": " + JSON.stringify(result.error));
  assert.ok(result.content.text.includes(marker), extension + " marker missing");
  pass(extension.toUpperCase() + ": extracts text from a synthetic archive fixture");
}

const rtfText = "CHRONO RTF FIXTURE";
const rtfResult = await readOfficeDocument({
  filename: "memo.rtf",
  contentType: "application/rtf",
  bytes: Buffer.from("{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Arial;}}\\pard " + rtfText + "\\par}", "utf8")
});
assert.equal(rtfResult.ok, true, JSON.stringify(rtfResult.error));
assert.ok(rtfResult.content.text.includes(rtfText), "RTF text missing");
pass("RTF: extracts text from a synthetic Rich Text Format document");

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
  fixtureTypes: ["DOCX", "PPTX", "XLSX", "ODT", "ODS", "ODP", "RTF", "EPUB"],
  networkCalls: 0,
  originalDocumentContentPrinted: false,
  defaultInputLimitBytes: 4 * 1024 * 1024
}, null, 2));
