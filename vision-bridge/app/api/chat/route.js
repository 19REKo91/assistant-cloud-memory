import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const WINDOW_MS = 60_000;
const MAX_REQUESTS = 10;
const requestsByIp = new Map();
const DEFAULT_WORKER_URL = "https://chatgpt-vision-bridge.flourish-gerbil.workers.dev/chat";

function json(data, status = 200) {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": "no-store, max-age=0" }
  });
}

function safeEqual(received, expected) {
  if (typeof received !== "string" || typeof expected !== "string") return false;
  const a = Buffer.from(received);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

function workerEndpoint() {
  const raw = process.env.YELLOW_CHAT_WORKER_URL || DEFAULT_WORKER_URL;
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return null;
    return url;
  } catch {
    return null;
  }
}

// Best-effort per-instance protection. The shared access token is the primary gate.
function allowedRequest(ip) {
  const now = Date.now();
  const entry = requestsByIp.get(ip);
  if (!entry || now - entry.start >= WINDOW_MS) {
    requestsByIp.set(ip, { start: now, count: 1 });
    return true;
  }
  if (entry.count >= MAX_REQUESTS) return false;
  entry.count += 1;
  return true;
}

export async function GET() {
  const accessToken = process.env.YELLOW_CHAT_ACCESS_TOKEN;
  const endpoint = workerEndpoint();
  if (!accessToken || !endpoint) {
    return json({ ok: true, configured: false });
  }

  try {
    const upstream = await fetch(endpoint, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(10_000)
    });
    const data = await upstream.json().catch(() => ({}));
    return json({
      ok: true,
      configured: Boolean(upstream.ok && data?.ok === true && data?.configured === true)
    });
  } catch {
    return json({ ok: true, configured: false });
  }
}

export async function POST(request) {
  const accessToken = process.env.YELLOW_CHAT_ACCESS_TOKEN;
  const endpoint = workerEndpoint();

  if (!accessToken || !endpoint) {
    return json({ ok: false, error: "chat_not_configured" }, 503);
  }

  const incomingToken = request.headers.get("x-yellow-chat-token") || "";
  if (!safeEqual(incomingToken, accessToken)) {
    return json({ ok: false, error: "unauthorized" }, 401);
  }

  const ip = (request.headers.get("x-forwarded-for") || "unknown").split(",")[0].trim();
  if (!allowedRequest(ip)) {
    return json({ ok: false, error: "rate_limited" }, 429);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "invalid_json" }, 400);
  }

  if (!Array.isArray(body?.messages) || body.messages.length < 1 || body.messages.length > 16) {
    return json({ ok: false, error: "invalid_messages" }, 400);
  }

  const messages = [];
  let totalLength = 0;
  for (const item of body.messages) {
    if (!item || !["user", "assistant"].includes(item.role) || typeof item.content !== "string") {
      return json({ ok: false, error: "invalid_messages" }, 400);
    }
    const content = item.content.trim();
    if (!content || content.length > 4000) {
      return json({ ok: false, error: "invalid_messages" }, 400);
    }
    totalLength += content.length;
    messages.push({ role: item.role, content });
  }

  if (totalLength > 20000 || messages[messages.length - 1]?.role !== "user") {
    return json({ ok: false, error: "invalid_messages" }, 400);
  }

  let upstream;
  try {
    upstream = await fetch(endpoint, {
      method: "POST",
      headers: {
        "x-bridge-token": accessToken,
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      cache: "no-store",
      signal: AbortSignal.timeout(70_000),
      body: JSON.stringify({ messages })
    });
  } catch {
    return json({ ok: false, error: "worker_unreachable" }, 502);
  }

  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok || data?.error) {
    if (data?.error === "unauthorized") {
      return json({ ok: false, error: "bridge_token_mismatch" }, 401);
    }
    if (data?.error === "chat_not_configured") {
      return json({ ok: false, error: "chat_not_configured" }, 503);
    }
    return json({ ok: false, error: "provider_error", status: upstream.status || 502 }, 502);
  }

  if (typeof data?.text !== "string" || !data.text.trim()) {
    return json({ ok: false, error: "provider_error" }, 502);
  }

  return json({ ok: true, text: data.text.trim() });
}
