#!/usr/bin/env node
// Read-only production smoke test for the public page and local PDF readers.
// Uses only a fixed public URL and a synthetic one-page PDF; never logs response content.
const ORIGIN = "https://chrono-cross-gpt.floot.app";
const PAGE_URL = new URL("/_api/read-page", ORIGIN);
const PDF_URL = new URL("/_api/read-pdf", ORIGIN);
const FIXTURE_TEXT = "CHRONO PDF SMOKE TEST";

function stop(stage, status, reason) {
  console.error(JSON.stringify({ ok: false, stage, httpStatus: status ?? null, reason, responseBodyPrinted: false }, null, 2));
  process.exit(1);
}

function buildPdf(text) {
  const stream = "BT /F1 18 Tf 72 720 Td (" + text + ") Tj ET";
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    "<< /Length " + Buffer.byteLength(stream, "ascii") + " >>\nstream\n" + stream + "\nendstream",
  ];
  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  for (let i = 0; i < objects.length; i++) {
    offsets.push(Buffer.byteLength(pdf, "ascii"));
    pdf += (i + 1) + " 0 obj\n" + objects[i] + "\nendobj\n";
  }
  const xrefOffset = Buffer.byteLength(pdf, "ascii");
  pdf += "xref\n0 " + (objects.length + 1) + "\n";
  pdf += "0000000000 65535 f \n";
  for (const offset of offsets.slice(1)) pdf += String(offset).padStart(10, "0") + " 00000 n \n";
  pdf += "trailer\n<< /Size " + (objects.length + 1) + " /Root 1 0 R >>\nstartxref\n" + xrefOffset + "\n%%EOF\n";
  return Buffer.from(pdf, "ascii");
}

function collectStrings(value, out = []) {
  if (typeof value === "string") out.push(value);
  else if (Array.isArray(value)) for (const item of value) collectStrings(item, out);
  else if (value && typeof value === "object") for (const item of Object.values(value)) collectStrings(item, out);
  return out;
}

async function main() {
  for (const [url, path] of [[PAGE_URL, "/_api/read-page"], [PDF_URL, "/_api/read-pdf"]]) {
    if (url.protocol !== "https:" || url.origin !== ORIGIN || url.pathname !== path) stop("endpoint_guard", null, "Refusing an unexpected test destination.");
  }

  const pageResponse = await fetch(PAGE_URL, {
    method: "POST",
    redirect: "error",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify({ url: "https://example.com/" }),
    signal: AbortSignal.timeout(25000),
  });
  const pageBody = await pageResponse.text();
  let pageData;
  try { pageData = JSON.parse(pageBody); } catch { stop("public_page_json", pageResponse.status, "Reader did not return JSON."); }
  const pageText = collectStrings(pageData).join("\n");
  if (!pageResponse.ok || !pageText.trim()) stop("public_page_read", pageResponse.status, "Public page extraction failed or returned no text.");
  if (/CHRONO_MCP_TOKEN|Bearer\s+[A-Za-z0-9._-]{20,}/i.test(pageText)) stop("public_page_redaction", pageResponse.status, "Unexpected credential-like output detected; body not logged.");

  const form = new FormData();
  form.append("file", new Blob([buildPdf(FIXTURE_TEXT)], { type: "application/pdf" }), "chrono-smoke.pdf");
  const pdfResponse = await fetch(PDF_URL, {
    method: "POST",
    redirect: "error",
    body: form,
    signal: AbortSignal.timeout(25000),
  });
  const pdfBody = await pdfResponse.text();
  let pdfData;
  try { pdfData = JSON.parse(pdfBody); } catch { stop("pdf_json", pdfResponse.status, "PDF reader did not return JSON."); }
  const pdfStrings = collectStrings(pdfData);
  const pdfTextFound = pdfStrings.some((s) => s.includes(FIXTURE_TEXT));
  if (!pdfResponse.ok || !pdfTextFound) stop("pdf_text_extraction", pdfResponse.status, "Synthetic PDF text was not found in the reader result.");

  console.log(JSON.stringify({
    ok: true,
    publicPage: { httpStatus: pageResponse.status, source: "https://example.com/", nonEmptyResult: true, responseBodyPrinted: false },
    localPdf: { httpStatus: pdfResponse.status, syntheticOnePageFixture: true, expectedTextFound: true, responseBodyPrinted: false },
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, stage: "network_or_runtime", errorType: error instanceof Error ? error.name : "unknown", message: "Reader smoke test failed; response content was not logged.", responseBodyPrinted: false }, null, 2));
  process.exitCode = 1;
});
