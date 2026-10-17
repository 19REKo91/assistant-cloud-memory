// Minimal authenticated HTTP bridge for repository-side document readers.
// Intended for a bounded deployment; it is not deployed or wired to Floot yet.
import { createServer } from "node:http";
import { timingSafeEqual } from "node:crypto";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { readDocument } from "./read-document.mjs";

const HARD_MAX_REQUEST_BYTES = 6 * 1024 * 1024;
const HARD_MAX_RESPONSE_BYTES = 2 * 1024 * 1024;
const HARD_MAX_CONCURRENCY = 8;
const DEFAULT_MAX_CONCURRENCY = 2;
const DEFAULT_REQUEST_TIMEOUT_MS = 15_000;

function jsonResponse(res, statusCode, payload, extraHeaders = {}) {
  const body = Buffer.from(JSON.stringify(payload), "utf8");
  res.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": String(body.length),
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    ...extraHeaders
  });
  res.end(body);
}

function errorResponse(res, statusCode, code, message, extraHeaders) {
  return jsonResponse(res, statusCode, {
    ok: false,
    error: { code, message },
    requestBodyLogged: false
  }, extraHeaders);
}

function isBearerTokenEqual(actualHeader, expectedToken) {
  if (typeof actualHeader !== "string") return false;
  const match = actualHeader.match(/^Bearer ([^\s]+)$/i);
  if (!match) return false;
  const actual = Buffer.from(match[1], "utf8");
  const expected = Buffer.from(expectedToken, "utf8");
  if (actual.length !== expected.length) return false;
  return timingSafeEqual(actual, expected);
}

function validConfiguredToken(token) {
  return typeof token === "string" && token.length >= 32 && !/\s/.test(token);
}

function readRequestBody(req, maximumBytes) {
  return new Promise((resolveBody, rejectBody) => {
    const chunks = [];
    let size = 0;
    let exceeded = false;
    let done = false;

    const rejectOnce = (error) => {
      if (done) return;
      done = true;
      rejectBody(error);
    };

    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > maximumBytes) {
        exceeded = true;
        chunks.length = 0;
      } else if (!exceeded) {
        chunks.push(chunk);
      }
    });
    req.on("end", () => {
      if (done) return;
      done = true;
      if (exceeded) {
        const error = new Error("body limit exceeded");
        error.code = "REQUEST_TOO_LARGE";
        rejectBody(error);
      } else {
        resolveBody(Buffer.concat(chunks, size));
      }
    });
    req.on("aborted", () => {
      const error = new Error("request aborted");
      error.code = "REQUEST_ABORTED";
      rejectOnce(error);
    });
    req.on("error", () => {
      const error = new Error("request stream failed");
      error.code = "REQUEST_STREAM_ERROR";
      rejectOnce(error);
    });
  });
}

function isSafeBase64(value) {
  if (typeof value !== "string" || value.length === 0 || value.length > HARD_MAX_REQUEST_BYTES) return false;
  if (value.length % 4 !== 0) return false;
  if (!/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) return false;
  return true;
}

function statusForReaderFailure(code) {
  if (code === "unsupported_type") return 415;
  if (code === "size_limit_exceeded") return 413;
  if (code === "provider_unavailable") return 503;
  if (code === "timeout") return 504;
  if (code === "malformed_input" || code === "empty_extraction" || code === "authentication_required") return 422;
  return 400;
}

/**
 * Options are injectable for deterministic tests. Production uses CHRONO_READER_BRIDGE_TOKEN.
 * POST /v1/read JSON body: { filename, contentType?, contentBase64 }.
 */
export function createReaderBridgeServer(options = {}) {
  const tokenProvider = typeof options.token === "function"
    ? options.token
    : () => (typeof options.token === "string" ? options.token : process.env.CHRONO_READER_BRIDGE_TOKEN);
  const reader = typeof options.reader === "function" ? options.reader : readDocument;
  const maxRequestBytes = Number.isSafeInteger(options.maxRequestBytes) && options.maxRequestBytes > 0
    ? Math.min(options.maxRequestBytes, HARD_MAX_REQUEST_BYTES)
    : HARD_MAX_REQUEST_BYTES;
  const maxResponseBytes = Number.isSafeInteger(options.maxResponseBytes) && options.maxResponseBytes > 0
    ? Math.min(options.maxResponseBytes, HARD_MAX_RESPONSE_BYTES)
    : HARD_MAX_RESPONSE_BYTES;
  const maxConcurrency = Number.isSafeInteger(options.maxConcurrency) && options.maxConcurrency > 0
    ? Math.min(options.maxConcurrency, HARD_MAX_CONCURRENCY)
    : DEFAULT_MAX_CONCURRENCY;
  let activeReads = 0;

  const server = createServer(async (req, res) => {
    if (req.method === "GET" && req.url === "/health") {
      return jsonResponse(res, 200, {
        ok: true,
        service: "chrono-cross-gpt-reader-bridge",
        status: "ready",
        authenticationRequiredForRead: true
      });
    }

    if (req.url !== "/v1/read") {
      return errorResponse(res, 404, "not_found", "Endpoint not found.");
    }
    if (req.method !== "POST") {
      return errorResponse(res, 405, "method_not_allowed", "Use POST for document reading.", { allow: "POST" });
    }

    const token = tokenProvider();
    if (!validConfiguredToken(token)) {
      return errorResponse(res, 503, "bridge_not_configured", "Document reader bridge authentication is not configured.");
    }
    if (!isBearerTokenEqual(req.headers.authorization, token)) {
      return errorResponse(res, 401, "authentication_required", "A valid Bearer token is required.", { "www-authenticate": 'Bearer realm="chrono-cross-gpt-reader"' });
    }

    const requestContentType = typeof req.headers["content-type"] === "string"
      ? req.headers["content-type"].split(";", 1)[0].trim().toLowerCase()
      : "";
    if (requestContentType !== "application/json") {
      return errorResponse(res, 415, "unsupported_type", "Send the document envelope as application/json.");
    }

    const declaredLength = Number(req.headers["content-length"]);
    if (Number.isFinite(declaredLength) && declaredLength > maxRequestBytes) {
      req.resume();
      return errorResponse(res, 413, "request_too_large", "The encoded request body exceeds the configured limit.", { connection: "close" });
    }
    if (activeReads >= maxConcurrency) {
      req.resume();
      return errorResponse(res, 429, "too_many_requests", "The reader is at its concurrency limit.", { "retry-after": "2" });
    }

    activeReads += 1;
    try {
      let bodyBytes;
      try {
        bodyBytes = await readRequestBody(req, maxRequestBytes);
      } catch (error) {
        if (error?.code === "REQUEST_TOO_LARGE") {
          return errorResponse(res, 413, "request_too_large", "The encoded request body exceeds the configured limit.");
        }
        return errorResponse(res, 400, "invalid_request", "The request body could not be read.");
      }

      let body;
      try {
        const bodyText = new TextDecoder("utf-8", { fatal: true }).decode(bodyBytes);
        body = JSON.parse(bodyText);
      } catch {
        return errorResponse(res, 400, "invalid_json", "The request body must be valid UTF-8 JSON.");
      }

      if (!body || typeof body !== "object" || Array.isArray(body)) {
        return errorResponse(res, 400, "invalid_request", "The request must be a JSON object.");
      }
      const keys = Object.keys(body);
      if (keys.some((key) => !["filename", "contentType", "contentBase64"].includes(key))) {
        return errorResponse(res, 400, "unexpected_fields", "Only filename, contentType and contentBase64 are allowed.");
      }
      if (typeof body.filename !== "string" || body.filename.length < 1 || body.filename.length > 512) {
        return errorResponse(res, 400, "invalid_filename", "A filename with a supported extension is required.");
      }
      if (body.contentType !== undefined && (typeof body.contentType !== "string" || body.contentType.length > 200)) {
        return errorResponse(res, 400, "invalid_content_type", "The content type value is invalid.");
      }
      if (!isSafeBase64(body.contentBase64)) {
        return errorResponse(res, 400, "invalid_base64", "contentBase64 must be a bounded, correctly padded Base64 string.");
      }

      const bytes = Buffer.from(body.contentBase64, "base64");
      if (bytes.length === 0) {
        return errorResponse(res, 400, "empty_file", "The uploaded file is empty.");
      }
      if (bytes.length > 4 * 1024 * 1024) {
        return errorResponse(res, 413, "file_too_large", "The decoded file exceeds the configured input limit.");
      }

      let result;
      try {
        result = await reader({
          filename: body.filename,
          contentType: body.contentType,
          bytes
        });
      } catch {
        return errorResponse(res, 500, "reader_failure", "The document reader failed without a safe result.");
      }

      const payload = {
        ok: result?.ok === true,
        result: result?.ok === true ? result : undefined,
        error: result?.ok === true ? undefined : result?.error
      };
      const responseBytes = Buffer.from(JSON.stringify(payload), "utf8");
      if (responseBytes.length > maxResponseBytes) {
        return errorResponse(res, 413, "response_too_large", "The extracted result exceeds the response limit; use a smaller file or a narrower extraction.");
      }
      const statusCode = result?.ok === true ? 200 : statusForReaderFailure(result?.error?.code);
      return jsonResponse(res, statusCode, payload);
    } finally {
      activeReads -= 1;
    }
  });

  server.requestTimeout = DEFAULT_REQUEST_TIMEOUT_MS;
  server.headersTimeout = DEFAULT_REQUEST_TIMEOUT_MS;
  server.keepAliveTimeout = 5_000;
  return server;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 8080);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    process.stderr.write("Invalid PORT configuration.\n");
    process.exit(1);
  }
  const server = createReaderBridgeServer();
  server.listen(port, "0.0.0.0", () => {
    process.stdout.write("CHRONO CROSS GPT reader bridge listening. Secrets are not logged.\n");
  });
}
