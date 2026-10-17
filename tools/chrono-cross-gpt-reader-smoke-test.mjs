#!/usr/bin/env node
// Read-only production smoke test for selectable-text PDF extraction and safe invalid-input handling.
// Uses synthetic fixtures only; never logs response content.
const ORIGIN = "https://chrono-cross-gpt.floot.app";
const PDF_URL = new URL("/_api/read-pdf", ORIGIN);
const FIXTURE_PAGES = [
  "CHRONO PDF SMOKE PAGE ONE",
  "CHRONO PDF SMOKE PAGE TWO",
];

function stop(stage, status, reason) {
  console.error(JSON.stringify({ ok: false, stage, httpStatus: status ?? null, reason, responseBodyPrinted: false }, null, 2));
  process.exit(1);
}

function escapePdfText(value) {
  return value.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function buildPdf(pageTexts) {
  if (!Array.isArray(pageTexts) || pageTexts.length < 1 || pageTexts.some((value) => typeof value !== "string" || !value.length)) {
    throw new TypeError("PDF fixture must have at least one non-empty page string.");
  }
  const count = pageTexts.length;
  const fontId = 3 + count;
  const firstContentId = fontId + 1;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [" + pageTexts.map((_, i) => (3 + i) + " 0 R").join(" ") + "] /Count " + count + " >>",
  ];
  for (let i = 0; i < count; i++) {
    objects.push(
      "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
      "/Resources << /Font << /F1 " + fontId + " 0 R >> >> " +
      "/Contents " + (firstContentId + i) + " 0 R >>"
    );
  }
  objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
  for (const text of pageTexts) {
    const stream = "BT /F1 18 Tf 72 720 Td (" + escapePdfText(text) + ") Tj ET";
    objects.push("<< /Length " + Buffer.byteLength(stream, "ascii") + " >>\nstream\n" + stream + "\nendstream");
  }

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
  if (PDF_URL.protocol !== "https:" || PDF_URL.origin !== ORIGIN || PDF_URL.pathname !== "/_api/read-pdf") {
    stop("endpoint_guard", null, "Refusing an unexpected test destination.");
  }

  async function upload(name, bytes, contentType) {
    const form = new FormData();
    form.append("file", new Blob([bytes], { type: contentType }), name);
    return fetch(PDF_URL, {
      method: "POST",
      redirect: "error",
      body: form,
      signal: AbortSignal.timeout(25000),
    });
  }

  const pdfResponse = await upload("chrono-smoke-multipage.pdf", buildPdf(FIXTURE_PAGES), "application/pdf");
  const pdfBody = await pdfResponse.text();
  let pdfData;
  try { pdfData = JSON.parse(pdfBody); } catch { stop("pdf_json", pdfResponse.status, "PDF reader did not return JSON."); }
  const pdfStrings = collectStrings(pdfData);
  const markersFound = FIXTURE_PAGES.map((marker) => pdfStrings.some((value) => value.includes(marker)));
  if (!pdfResponse.ok || markersFound.some((found) => !found)) {
    stop("multipage_pdf_extraction", pdfResponse.status, "The reader did not return both unique text markers from the synthetic two-page PDF.");
  }

  const malformedResponse = await upload(
    "malformed.pdf",
    Buffer.from("%PDF-1.4\\nnot a valid PDF structure\\n%%EOF\\n", "ascii"),
    "application/pdf",
  );
  await malformedResponse.body?.cancel();
  if (malformedResponse.status < 400 || malformedResponse.status >= 500) {
    stop("malformed_pdf_rejection", malformedResponse.status, "Malformed PDF should be rejected with a client error, not accepted or surfaced as a server error.");
  }

  const unsupportedResponse = await upload("not-a-pdf.txt", Buffer.from("plain text, not a PDF", "utf8"), "text/plain");
  await unsupportedResponse.body?.cancel();
  if (unsupportedResponse.status < 400 || unsupportedResponse.status >= 500) {
    stop("unsupported_file_rejection", unsupportedResponse.status, "A non-PDF upload should be rejected with a client error.");
  }

  console.log(JSON.stringify({
    ok: true,
    localPdf: {
      httpStatus: pdfResponse.status,
      syntheticPageCount: FIXTURE_PAGES.length,
      expectedMarkersFound: markersFound.length,
      bothPageMarkersFound: true,
      responseBodyPrinted: false,
    },
    malformedPdf: { httpStatus: malformedResponse.status, rejectedWithClientError: true, responseBodyPrinted: false },
    unsupportedUpload: { httpStatus: unsupportedResponse.status, rejectedWithClientError: true, responseBodyPrinted: false },
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, stage: "network_or_runtime", errorType: error instanceof Error ? error.name : "unknown", message: "Reader smoke test failed; response content was not logged.", responseBodyPrinted: false }, null, 2));
  process.exitCode = 1;
});
