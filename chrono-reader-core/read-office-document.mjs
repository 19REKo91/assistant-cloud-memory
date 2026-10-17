// Repository-side Office / ebook reader. Not yet wired into the live Floot app.
import { OfficeParser } from "officeparser";

const HARD_MAX_INPUT_BYTES = 4 * 1024 * 1024;
const HARD_MAX_OUTPUT_CHARS = 1_000_000;
const HARD_MAX_TIMEOUT_MS = 10_000;
const SUPPORTED = Object.freeze({
  ".docx": { fileType: "docx", formats: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"] },
  ".pptx": { fileType: "pptx", formats: ["application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/octet-stream"] },
  ".xlsx": { fileType: "xlsx", formats: ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream"] },
  ".odt": { fileType: "odt", formats: ["application/vnd.oasis.opendocument.text", "application/octet-stream"] },
  ".ods": { fileType: "ods", formats: ["application/vnd.oasis.opendocument.spreadsheet", "application/octet-stream"] },
  ".odp": { fileType: "odp", formats: ["application/vnd.oasis.opendocument.presentation", "application/octet-stream"] },
  ".rtf": { fileType: "rtf", formats: ["application/rtf", "text/rtf", "application/octet-stream"] },
  ".epub": { fileType: "epub", formats: ["application/epub+zip", "application/octet-stream"] }
});

function safeFilename(value) {
  if (typeof value !== "string") return "";
  return (value.split(/[\\/]/).pop() ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .trim()
    .slice(0, 128);
}

function parseMediaType(value) {
  if (typeof value !== "string") return "";
  return value.split(";", 1)[0].trim().toLowerCase();
}

function stableError(code, message, retryable = false) {
  return { code, message, retryable };
}

function failure(source, code, message, retryable = false, warnings = []) {
  return {
    ok: false,
    source,
    method: "officeparser",
    completeness: "unavailable",
    content: null,
    references: [],
    warnings,
    error: stableError(code, message, retryable)
  };
}

function safeParserWarning(warning) {
  const candidate = warning && typeof warning === "object"
    ? (warning.code ?? warning.type ?? warning.name)
    : null;
  const code = typeof candidate === "string" && /^[A-Z][A-Z0-9_]{1,79}$/.test(candidate)
    ? candidate
    : "PARSER_WARNING";
  return { code };
}

function mapParserError(error) {
  if (error?.name === "AbortError") {
    return { code: "timeout", message: "Document parsing exceeded the configured time limit.", retryable: true };
  }
  const code = typeof error?.code === "string" ? error.code.toUpperCase() : "";
  if (/PASSWORD_REQUIRED|PASSWORD_INCORRECT|DOCUMENT_DECRYPTION_FAILED/.test(code)) {
    return { code: "authentication_required", message: "This document is encrypted or password-protected; password entry is not handled by this reader.", retryable: false };
  }
  if (/ZIP_SIZE_LIMIT|ZIP_ENTRY_COUNT_LIMIT|XML_ELEMENT_LIMIT|TABLE_CELL_LIMIT|REPEATED_CONTENT_LIMIT|RAW_CONTENT_LIMIT/.test(code)) {
    return { code: "size_limit_exceeded", message: "The document exceeded a safe parsing limit.", retryable: false };
  }
  if (/UNSUPPORTED_FORMAT|FILE_TYPE_DETECTION_FAILED|BUFFER_TYPE_MISMATCH/.test(code)) {
    return { code: "unsupported_type", message: "The file content does not match a supported document format.", retryable: false };
  }
  if (/ABORT|TIMEOUT|EMBEDDING_TIMEOUT/.test(code)) {
    return { code: "timeout", message: "Document parsing timed out.", retryable: true };
  }
  return { code: "malformed_input", message: "The document could not be parsed. It may be damaged or not match its extension.", retryable: false };
}

function boundedInteger(value, fallback, maximum) {
  return Number.isSafeInteger(value) && value > 0 ? Math.min(value, maximum) : fallback;
}

function noContent(text, warnings) {
  return !text.trim() || warnings.some((warning) =>
    ["PDF_NO_TEXT_EXTRACTED", "CONTENT_PART_NOT_READ", "NO_WORKSHEETS_FOUND", "NO_SLIDES_FOUND"].includes(warning.code)
  );
}

/**
 * input = { filename, contentType?, bytes: Buffer | Uint8Array, limits? }
 * Supports only allowlisted document extensions, never arbitrary .zip archives.
 */
export async function readOfficeDocument(input) {
  const candidate = input && typeof input === "object" ? input : {};
  const filename = safeFilename(candidate.filename);
  const dot = filename.lastIndexOf(".");
  const extension = dot >= 0 ? filename.slice(dot).toLowerCase() : "";
  const config = SUPPORTED[extension];
  const providedType = parseMediaType(candidate.contentType);
  const isBytes = Buffer.isBuffer(candidate.bytes) || candidate.bytes instanceof Uint8Array;
  const byteSize = isBytes ? candidate.bytes.byteLength : null;
  const source = {
    kind: "uploaded_file",
    filename: filename || "uploaded-file",
    mediaType: providedType || config?.formats[0] || "application/octet-stream",
    byteSize
  };

  if (!filename || filename === "." || filename === "..") {
    return failure(source, "malformed_input", "A filename with a supported extension is required.");
  }
  if (!config) {
    return failure(source, "unsupported_type", "This reader supports DOCX, PPTX, XLSX, ODT, ODS, ODP, RTF and EPUB only.");
  }
  if (!isBytes) {
    return failure(source, "malformed_input", "File bytes must be supplied as a byte buffer.");
  }
  if (byteSize === 0) {
    return failure(source, "empty_extraction", "The uploaded file is empty.");
  }
  const maxBytes = boundedInteger(candidate.limits?.maxBytes, HARD_MAX_INPUT_BYTES, HARD_MAX_INPUT_BYTES);
  if (byteSize > maxBytes) {
    return failure(source, "size_limit_exceeded", "The uploaded file exceeds the configured byte limit.");
  }
  if (providedType && !config.formats.includes(providedType)) {
    return failure(source, "unsupported_type", "The declared media type does not match the file extension.");
  }

  const limits = candidate.limits && typeof candidate.limits === "object" ? candidate.limits : {};
  const maxOutputChars = boundedInteger(limits.maxOutputChars, 250_000, HARD_MAX_OUTPUT_CHARS);
  const timeoutMs = boundedInteger(limits.timeoutMs, 8_000, HARD_MAX_TIMEOUT_MS);
  const maxUncompressedBytes = boundedInteger(limits.maxUncompressedBytes, 24 * 1024 * 1024, 32 * 1024 * 1024);
  const maxZipEntries = boundedInteger(limits.maxZipEntries, 512, 1024);
  const maxXmlElements = boundedInteger(limits.maxXmlElements, 100_000, 200_000);
  const maxTableCells = boundedInteger(limits.maxTableCells, 20_000, 50_000);
  const maxRepeatedContent = boundedInteger(limits.maxRepeatedContent, 2 * 1024 * 1024, 4 * 1024 * 1024);

  const buffer = Buffer.isBuffer(candidate.bytes) ? candidate.bytes : Buffer.from(candidate.bytes);
  const warnings = [];
  try {
    const ast = await OfficeParser.parseOffice(buffer, {
      fileType: config.fileType,
      abortSignal: AbortSignal.timeout(timeoutMs),
      includeRawContent: false,
      extractAttachments: false,
      ocr: false,
      decompressionLimits: {
        maxUncompressedBytes,
        maxZipEntries,
        maxXmlElements,
        maxTableCells,
        maxRepeatedContent,
        maxRawContentLength: 0
      }
    });

    const parserWarnings = Array.isArray(ast?.warnings) ? ast.warnings.map(safeParserWarning) : [];
    warnings.push(...parserWarnings);
    const converted = await ast.to("md", { includeFormatting: false });
    let text = typeof converted?.value === "string" ? converted.value : "";
    if (!text.trim()) {
      const plain = await ast.to("text", {
        includeImages: false,
        textConfig: { preserveLayout: false, renderNotes: true }
      });
      text = typeof plain?.value === "string" ? plain.value : "";
    }

    if (!text.trim()) {
      return failure(source, "empty_extraction", "No readable text was extracted from the document.", false, warnings);
    }
    const truncated = text.length > maxOutputChars;
    if (truncated) {
      text = text.slice(0, maxOutputChars);
      warnings.push({ code: "OUTPUT_TRUNCATED" });
    }
    const parserPartial = parserWarnings.length > 0 || truncated;
    const completeness = parserPartial ? "partial" : "complete";
    const extensionReferences = extension === ".pptx"
      ? [{ kind: "scope", value: "slide text; slide-by-slide citations are not yet exposed by this adapter" }]
      : extension === ".xlsx" || extension === ".ods"
        ? [{ kind: "scope", value: "spreadsheet text; per-sheet and per-cell citations are not yet exposed by this adapter" }]
        : [];

    return {
      ok: true,
      source: { ...source, detectedType: typeof ast?.type === "string" ? ast.type : config.fileType },
      method: "officeparser",
      completeness,
      content: {
        type: "markdown",
        text,
        characterCount: text.length,
        truncated
      },
      references: extensionReferences,
      warnings,
      error: null
    };
  } catch (error) {
    const mapped = mapParserError(error);
    return failure(source, mapped.code, mapped.message, mapped.retryable, warnings);
  }
}

export const OFFICE_DOCUMENT_READER_LIMITS = Object.freeze({
  maxInputBytes: HARD_MAX_INPUT_BYTES,
  maxOutputChars: HARD_MAX_OUTPUT_CHARS,
  maxTimeoutMs: HARD_MAX_TIMEOUT_MS,
  defaultUncompressedBytes: 24 * 1024 * 1024,
  defaultZipEntries: 512,
  defaultXmlElements: 100_000,
  defaultTableCells: 20_000
});
