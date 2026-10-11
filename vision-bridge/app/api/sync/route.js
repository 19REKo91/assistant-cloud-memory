import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const OWNER = "19REKo91";
const REPO = "assistant-cloud-memory";
const FILE_PATH = "SYNC/DEEPSEEK_REPLY.md";
const CONTENTS_URL = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE_PATH}`;
const FILE_URL = `https://github.com/${OWNER}/${REPO}/blob/main/${FILE_PATH}`;
const NO_STORE = { "Cache-Control": "no-store, no-cache, must-revalidate" };

function json(data, status = 200) {
  return Response.json(data, { status, headers: NO_STORE });
}

function constantTimeEqual(a, b) {
  const left = Buffer.from(a, "utf8");
  const right = Buffer.from(b, "utf8");
  return left.length === right.length && timingSafeEqual(left, right);
}

function githubHeaders(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "assistant-cloud-memory-relay"
  };
}

// Public status only. Never returns either secret.
export async function GET() {
  const configured = Boolean(
    process.env.GITHUB_SYNC_TOKEN?.trim() &&
    process.env.SYNC_WRITE_KEY
  );

  return json({
    ok: true,
    service: "github-reply-relay",
    configured,
    target: FILE_PATH
  });
}

export async function POST(request) {
  const token = process.env.GITHUB_SYNC_TOKEN?.trim() || "";
  const expectedKey = process.env.SYNC_WRITE_KEY || "";

  // Fail closed until both server-side secrets have been configured.
  if (!token || !expectedKey) {
    return json({ error: "sync_not_configured" }, 503);
  }

  const suppliedKey = request.headers.get("x-sync-write-key") || "";
  if (!suppliedKey || !constantTimeEqual(suppliedKey, expectedKey)) {
    return json({ error: "unauthorized" }, 401);
  }

  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > 125_000) {
    return json({ error: "request_too_large" }, 413);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  if (typeof body?.content !== "string" || !body.content.trim()) {
    return json({ error: "content_required" }, 400);
  }

  const content = body.content.trim();
  if (Buffer.byteLength(content, "utf8") > 100_000) {
    return json({ error: "content_too_large" }, 413);
  }

  const headers = githubHeaders(token);
  let existingSha = null;

  try {
    const current = await fetch(CONTENTS_URL, {
      method: "GET",
      headers,
      cache: "no-store"
    });

    if (current.ok) {
      const currentJson = await current.json();
      existingSha = typeof currentJson?.sha === "string" ? currentJson.sha : null;
      if (!existingSha) return json({ error: "github_read_invalid_response" }, 502);
    } else if (current.status !== 404) {
      return json({ error: "github_read_failed", status: current.status }, 502);
    }

    const writeHeaders = {
      ...headers,
      "Content-Type": "application/json"
    };

    const putBody = {
      message: "Save latest DeepSeek relay reply",
      content: Buffer.from(content + "\n", "utf8").toString("base64")
    };
    if (existingSha) putBody.sha = existingSha;

    const written = await fetch(CONTENTS_URL, {
      method: "PUT",
      headers: writeHeaders,
      body: JSON.stringify(putBody),
      cache: "no-store"
    });

    let result = {};
    try {
      result = await written.json();
    } catch {
      return json({ error: "github_write_invalid_response" }, 502);
    }

    if (!written.ok) {
      return json({ error: "github_write_failed", status: written.status }, 502);
    }

    return json({
      ok: true,
      path: FILE_PATH,
      url: result?.content?.html_url || FILE_URL,
      commit_sha: result?.commit?.sha || null
    });
  } catch {
    return json({ error: "github_unreachable" }, 502);
  }
}
