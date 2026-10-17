// Dependency-free, bounded readers for uploaded UTF-8 text-like documents.
// Repository-side adapter only: it is not yet wired into the published Floot app.
const MAX_BYTES_HARD = 1024 * 1024;
const MAX_ROWS_HARD = 10_000;
const MAX_COLUMNS_HARD = 256;
const MAX_CELLS_HARD = 50_000;
const MAX_JSON_DEPTH_HARD = 40;
const MAX_JSON_NODES_HARD = 50_000;

export const DEFAULT_TEXT_READER_LIMITS = Object.freeze({
  maxBytes: MAX_BYTES_HARD,
  maxRows: MAX_ROWS_HARD,
  maxColumns: MAX_COLUMNS_HARD,
  maxCells: MAX_CELLS_HARD,
  maxJsonDepth: MAX_JSON_DEPTH_HARD,
  maxJsonNodes: MAX_JSON_NODES_HARD,
});

const MIME_BY_EXTENSION = Object.freeze({
  ".txt": new Set(["text/plain", "application/octet-stream"]),
  ".md": new Set(["text/markdown", "text/x-markdown", "text/plain", "application/octet-stream"]),
  ".markdown": new Set(["text/markdown", "text/x-markdown", "text/plain", "application/octet-stream"]),
  ".csv": new Set(["text/csv", "application/csv", "text/plain", "application/octet-stream"]),
  ".json": new Set(["application/json", "text/json", "text/plain", "application/octet-stream"]),
});

function boundedLimit(value, fallback, hardMaximum) {
  if (!Number.isSafeInteger(value) || value < 1) return fallback;
  return Math.min(value, hardMaximum);
}

function safeFilename(filename) {
  if (typeof filename !== "string") return "";
  const basename = filename.split(/[\\/]/).pop() ?? "";
  return basename.replace(/[\u0000-\u001f\u007f]/g, "").trim().slice(0, 128);
}

function normalizedMediaType(contentType, extension) {
  const raw = typeof contentType === "string" ? contentType : "";
  const mediaType = raw.split(";", 1)[0].trim().toLowerCase();
  if (mediaType) return mediaType;
  if (extension === ".json") return "application/json";
  if (extension === ".csv") return "text/csv";
  if (extension === ".md" || extension === ".markdown") return "text/markdown";
  if (extension === ".txt") return "text/plain";
  return "application/octet-stream";
}

function failure(source, code, message, retryable = false) {
  return {
    ok: false,
    source,
    method: "utf8-text-document-reader",
    completeness: "unavailable",
    content: null,
    references: [],
    warnings: [],
    error: { code, message, retryable },
  };
}

function makeSource(filename, mediaType, byteSize) {
  return { kind: "uploaded_file", filename, mediaType, byteSize };
}

function resolveLimits(inputLimits) {
  const supplied = inputLimits && typeof inputLimits === "object" ? inputLimits : {};
  return {
    maxBytes: boundedLimit(supplied.maxBytes, MAX_BYTES_HARD, MAX_BYTES_HARD),
    maxRows: boundedLimit(supplied.maxRows, MAX_ROWS_HARD, MAX_ROWS_HARD),
    maxColumns: boundedLimit(supplied.maxColumns, MAX_COLUMNS_HARD, MAX_COLUMNS_HARD),
    maxCells: boundedLimit(supplied.maxCells, MAX_CELLS_HARD, MAX_CELLS_HARD),
    maxJsonDepth: boundedLimit(supplied.maxJsonDepth, MAX_JSON_DEPTH_HARD, MAX_JSON_DEPTH_HARD),
    maxJsonNodes: boundedLimit(supplied.maxJsonNodes, MAX_JSON_NODES_HARD, MAX_JSON_NODES_HARD),
  };
}

function parseCsv(text, limits) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  let afterQuote = false;
  let pending = false;
  let totalCells = 0;

  const pushField = () => {
    row.push(field);
    totalCells += 1;
    if (row.length > limits.maxColumns) {
      const error = new Error("CSV column limit exceeded");
      error.code = "size_limit_exceeded";
      throw error;
    }
    if (totalCells > limits.maxCells) {
      const error = new Error("CSV cell limit exceeded");
      error.code = "size_limit_exceeded";
      throw error;
    }
    field = "";
    pending = false;
    afterQuote = false;
  };

  const pushRow = () => {
    pushField();
    rows.push(row);
    if (rows.length > limits.maxRows) {
      const error = new Error("CSV row limit exceeded");
      error.code = "size_limit_exceeded";
      throw error;
    }
    row = [];
    field = "";
    pending = false;
    afterQuote = false;
  };

  for (let i = 0; i < text.length; i += 1) {
    const character = text[i];

    if (inQuotes) {
      if (character === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          inQuotes = false;
          afterQuote = true;
        }
      } else {
        field += character;
      }
      continue;
    }

    if (afterQuote) {
      if (character === ",") {
        pushField();
        pending = true;
        continue;
      }
      if (character === "\n" || character === "\r") {
        if (character === "\r" && text[i + 1] === "\n") i += 1;
        pushRow();
        continue;
      }
      if (character === " " || character === "\t") continue;
      const error = new Error("Unexpected character after closing CSV quote");
      error.code = "malformed_input";
      throw error;
    }

    if (character === ",") {
      pushField();
      pending = true;
      continue;
    }
    if (character === "\n" || character === "\r") {
      if (character === "\r" && text[i + 1] === "\n") i += 1;
      pushRow();
      continue;
    }
    if (character === '"') {
      if (field.length !== 0) {
        const error = new Error("CSV quote occurred inside an unquoted field");
        error.code = "malformed_input";
        throw error;
      }
      inQuotes = true;
      pending = true;
      continue;
    }
    field += character;
    pending = true;
  }

  if (inQuotes) {
    const error = new Error("CSV contains an unterminated quoted field");
    error.code = "malformed_input";
    throw error;
  }
  if (pending || field.length > 0 || row.length > 0 || afterQuote) pushRow();
  if (rows.length === 0) {
    const error = new Error("CSV has no records");
    error.code = "empty_extraction";
    throw error;
  }

  const headers = rows[0];
  const dataRows = rows.slice(1).map((cells, index) => ({ rowNumber: index + 2, cells }));
  const warnings = dataRows
    .filter((record) => record.cells.length !== headers.length)
    .map((record) => ({
      code: "ragged_row",
      message: "CSV row " + record.rowNumber + " has a different number of cells than the header row.",
    }));

  return {
    type: "table",
    format: "csv",
    headers,
    rows: dataRows,
    rowCount: dataRows.length,
    columnCount: headers.length,
    warnings,
  };
}

function countJsonNodesAndDepth(root, limits) {
  const stack = [{ value: root, depth: 0 }];
  let nodeCount = 0;
  while (stack.length) {
    const current = stack.pop();
    nodeCount += 1;
    if (nodeCount > limits.maxJsonNodes) {
      return { ok: false, code: "size_limit_exceeded", message: "JSON structure exceeds the configured complexity limit." };
    }
    if (current.depth > limits.maxJsonDepth) {
      return { ok: false, code: "size_limit_exceeded", message: "JSON nesting exceeds the configured depth limit." };
    }
    if (Array.isArray(current.value)) {
      for (const child of current.value) stack.push({ value: child, depth: current.depth + 1 });
    } else if (current.value !== null && typeof current.value === "object") {
      for (const child of Object.values(current.value)) stack.push({ value: child, depth: current.depth + 1 });
    }
  }
  return { ok: true, nodeCount };
}

/**
 * Read a bounded text-like file.
 * input: { filename: string, contentType?: string, bytes: Buffer|Uint8Array, limits?: object }
 * Returns a stable result envelope and never includes raw input in failure messages.
 */
export function readTextDocument(input) {
  const candidate = input && typeof input === "object" ? input : {};
  const filename = safeFilename(candidate.filename);
  const extension = filename.includes(".") ? filename.slice(filename.lastIndexOf(".")).toLowerCase() : "";
  const mediaType = normalizedMediaType(candidate.contentType, extension);
  const bufferLike = Buffer.isBuffer(candidate.bytes) || candidate.bytes instanceof Uint8Array;
  const byteSize = bufferLike ? candidate.bytes.byteLength : null;
  const source = makeSource(filename || "uploaded-file", mediaType, byteSize);
  const limits = resolveLimits(candidate.limits);

  if (!filename || filename === "." || filename === "..") {
    return failure(source, "malformed_input", "A filename is required to identify the document type.");
  }
  if (!bufferLike) {
    return failure(source, "malformed_input", "File bytes must be supplied as a byte buffer.");
  }
  if (byteSize === 0) {
    return failure(source, "empty_extraction", "The uploaded file is empty.");
  }
  // Check the declared byte view before copying a Uint8Array into a Buffer.
  if (byteSize > limits.maxBytes) {
    return failure(source, "size_limit_exceeded", "The uploaded file exceeds the configured byte limit.");
  }
  const buffer = Buffer.isBuffer(candidate.bytes) ? candidate.bytes : Buffer.from(candidate.bytes);
  if (buffer.includes(0)) {
    return failure(source, "malformed_input", "Binary or NUL-containing data is not supported by this text reader.");
  }
  const allowedTypes = MIME_BY_EXTENSION[extension];
  if (!allowedTypes) {
    return failure(source, "unsupported_type", "This file extension is not supported by the text document reader.");
  }
  if (!allowedTypes.has(mediaType)) {
    return failure(source, "unsupported_type", "The declared media type does not match a supported text document type.");
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  } catch {
    return failure(source, "malformed_input", "The file is not valid UTF-8 text.");
  }
  if (!text.trim()) {
    return failure(source, "empty_extraction", "No readable text was found in the uploaded file.");
  }

  let content;
  let warnings = [];
  let references = [];
  if (extension === ".csv") {
    try {
      content = parseCsv(text, limits);
      warnings = content.warnings;
      if (content.rowCount > 0) references.push({ kind: "row_range", startRow: 2, endRow: content.rowCount + 1 });
    } catch (error) {
      const code = error && ["malformed_input", "size_limit_exceeded", "empty_extraction"].includes(error.code)
        ? error.code
        : "malformed_input";
      return failure(source, code, code === "size_limit_exceeded"
        ? "CSV structure exceeds the configured row, column, or cell limit."
        : code === "empty_extraction"
          ? "No CSV records were found."
          : "CSV syntax is malformed.");
    }
  } else if (extension === ".json") {
    let value;
    try {
      value = JSON.parse(text);
    } catch {
      return failure(source, "malformed_input", "JSON syntax is malformed.");
    }
    const complexity = countJsonNodesAndDepth(value, limits);
    if (!complexity.ok) return failure(source, complexity.code, complexity.message);
    content = { type: "json", value, nodeCount: complexity.nodeCount };
  } else if (extension === ".md" || extension === ".markdown") {
    const lines = text.split(/\r\n|\r|\n/);
    const headings = [];
    for (let index = 0; index < lines.length; index += 1) {
      const match = lines[index].match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (match) headings.push({ level: match[1].length, text: match[2].trim(), line: index + 1 });
    }
    content = { type: "markdown", text, lineCount: lines.length, headings };
    references = headings.map((heading) => ({ kind: "heading_line", title: heading.text, line: heading.line }));
    if (references.length === 0) references.push({ kind: "line_range", startLine: 1, endLine: lines.length });
  } else {
    const lines = text.split(/\r\n|\r|\n/);
    content = { type: "text", text, lineCount: lines.length };
    references.push({ kind: "line_range", startLine: 1, endLine: lines.length });
  }

  return {
    ok: true,
    source,
    method: "utf8-text-document-reader",
    completeness: "complete",
    content,
    references,
    warnings,
    error: null,
  };
}
