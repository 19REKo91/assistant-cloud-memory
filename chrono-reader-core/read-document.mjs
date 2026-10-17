// Unified bounded file-reader router. Repository-side only; not yet wired to the live product.
import { readTextDocument } from "./read-text-document.mjs";
import { readOfficeDocument } from "./read-office-document.mjs";

const TEXT_EXTENSIONS = new Set([".txt", ".md", ".markdown", ".csv", ".json"]);
const OFFICE_EXTENSIONS = new Set([".docx", ".pptx", ".xlsx", ".odt", ".ods", ".odp", ".rtf", ".epub"]);

function getExtension(filename) {
  if (typeof filename !== "string") return "";
  const safeName = filename.split(/[\\/]/).pop() ?? "";
  const index = safeName.lastIndexOf(".");
  return index >= 0 ? safeName.slice(index).toLowerCase() : "";
}

function normalizedSource(input) {
  const fileName = typeof input?.filename === "string" ? (input.filename.split(/[\\/]/).pop() ?? "") : "uploaded-file";
  const type = typeof input?.contentType === "string" ? input.contentType.split(";", 1)[0].trim().toLowerCase() : "application/octet-stream";
  const isBytes = Buffer.isBuffer(input?.bytes) || input?.bytes instanceof Uint8Array;
  return {
    kind: "uploaded_file",
    filename: fileName.replace(/[\u0000-\u001f\u007f]/g, "").slice(0, 128) || "uploaded-file",
    mediaType: type || "application/octet-stream",
    byteSize: isBytes ? input.bytes.byteLength : null
  };
}

function failure(source, code, message) {
  return {
    ok: false,
    source,
    method: "document-router",
    completeness: "unavailable",
    content: null,
    references: [],
    warnings: [],
    error: { code, message, retryable: false }
  };
}

/**
 * Routes supported files to their reader based only on an allowlisted extension.
 * This router never fetches URLs, expands arbitrary ZIP files, or executes document content.
 */
export async function readDocument(input) {
  const source = normalizedSource(input);
  const extension = getExtension(input?.filename);

  if (!input || typeof input !== "object") {
    return failure(source, "malformed_input", "File metadata and bytes are required.");
  }
  if (!extension) {
    return failure(source, "unsupported_type", "A supported filename extension is required to select a reader.");
  }
  if (TEXT_EXTENSIONS.has(extension)) return readTextDocument(input);
  if (OFFICE_EXTENSIONS.has(extension)) return readOfficeDocument(input);
  if (extension === ".pdf") {
    return failure(source, "provider_unavailable", "PDF uploads are currently handled by the published PDF endpoint; this repository-side router does not replace that service.");
  }
  return failure(source, "unsupported_type", "No reader is registered for this file extension.");
}

export function getDocumentReaderCapabilities() {
  return {
    routerStatus: "repository_only",
    readers: [
      { id: "text.utf8", extensions: [".txt"], status: "implemented_tested_offline" },
      { id: "text.markdown", extensions: [".md", ".markdown"], status: "implemented_tested_offline" },
      { id: "text.csv", extensions: [".csv"], status: "implemented_tested_offline" },
      { id: "text.json", extensions: [".json"], status: "implemented_tested_offline" },
      { id: "office.word", extensions: [".docx"], status: "implemented_tested_offline" },
      { id: "office.presentation", extensions: [".pptx"], status: "implemented_tested_offline" },
      { id: "office.spreadsheet", extensions: [".xlsx"], status: "implemented_tested_offline" },
      { id: "office.odf", extensions: [".odt", ".ods", ".odp"], status: "implemented_unverified" },
      { id: "office.rtf", extensions: [".rtf"], status: "implemented_tested_offline" },
      { id: "book.epub", extensions: [".epub"], status: "implemented_unverified" },
      { id: "pdf.production", extensions: [".pdf"], status: "delegated_to_existing_endpoint" }
    ],
    unavailableHere: ["legacy .doc", "scanned PDF OCR", "image OCR", "audio/video transcription", "browser-rendered DOM"]
  };
}
