import { randomUUID, timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const OWNER = "19REKo91";
const REPO = "assistant-cloud-memory";
const API_ROOT = `https://api.github.com/repos/${OWNER}/${REPO}/contents`;
const NO_STORE = { "Cache-Control": "no-store, no-cache, must-revalidate" };
const MAX_CONTENT_BYTES = 90_000;

function json(data, status = 200) {
  return Response.json(data, { status, headers: NO_STORE });
}

function safeEqual(received, expected) {
  if (typeof received !== "string" || typeof expected !== "string") return false;
  const left = Buffer.from(received, "utf8");
  const right = Buffer.from(expected, "utf8");
  return left.length === right.length && timingSafeEqual(left, right);
}

function githubHeaders(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "assistant-cloud-memory-android-archive"
  };
}

export async function GET() {
  const configured = Boolean(
    process.env.GITHUB_SYNC_TOKEN?.trim() &&
    process.env.SYNC_WRITE_KEY
  );
  return json({ ok: true, service: "raeq-response-archive", configured });
}

export async function POST(request) {
  const token = process.env.GITHUB_SYNC_TOKEN?.trim() || "";
  const expectedKey = process.env.SYNC_WRITE_KEY || "";

  if (!token || !expectedKey) {
    return json({ ok: false, error: "sync_not_configured" }, 503);
  }

  const suppliedKey = request.headers.get("x-sync-write-key") || "";
  if (!safeEqual(suppliedKey, expectedKey)) {
    return json({ ok: false, error: "unauthorized" }, 401);
  }

  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > 125_000) {
    return json({ ok: false, error: "request_too_large" }, 413);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "invalid_json" }, 400);
  }

  if (typeof body?.content !== "string" || !body.content.trim()) {
    return json({ ok: false, error: "content_required" }, 400);
  }

  const answer = body.content.trim();
  if (Buffer.byteLength(answer, "utf8") > MAX_CONTENT_BYTES) {
    return json({ ok: false, error: "content_too_large" }, 413);
  }

  const savedAt = new Date();
  const iso = savedAt.toISOString();
  const date = iso.slice(0, 10);
  const time = iso.slice(11, 19).replaceAll(":", "-");
  const path = `SYNC/DEEPSEEK_LOG/${date}/${time}-${randomUUID().slice(0, 8)}.md`;
  const content = [
    "# DeepSeek response",
    "",
    `- Saved at (UTC): ${iso}`,
    "- Source: Android share bridge",
    "",
    "---",
    "",
    answer,
    ""
  ].join("\n");

  try {
    const response = await fetch(`${API_ROOT}/${path}`, {
      method: "PUT",
      headers: {
        ...githubHeaders(token),
        "Content-Type": "application/json"
      },
      cache: "no-store",
      body: JSON.stringify({
        message: `Archive DeepSeek response ${iso}`,
        content: Buffer.from(content, "utf8").toString("base64")
      }),
      signal: AbortSignal.timeout(25_000)
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      return json({
        ok: false,
        error: "github_write_failed",
        status: response.status
      }, 502);
    }

    const url = result?.content?.html_url ||
      `https://github.com/${OWNER}/${REPO}/blob/main/${path}`;

    return json({
      ok: true,
      path,
      url,
      commit_sha: result?.commit?.sha || null
    });
  } catch {
    return json({ ok: false, error: "github_unreachable" }, 502);
  }
}
