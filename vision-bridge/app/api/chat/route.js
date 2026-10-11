import { timingSafeEqual } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const WINDOW_MS = 60_000;
const MAX_REQUESTS = 10;
const requestsByIp = new Map();

function json(data, status = 200) {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": "no-store, max-age=0" }
  });
}

export async function GET() {
  const configured = Boolean(process.env.OPENAI_API_KEY && process.env.YELLOW_CHAT_ACCESS_TOKEN);
  return json({ ok: true, configured });
}

function safeEqual(received, expected) {
  if (typeof received !== "string" || typeof expected !== "string") return false;
  const a = Buffer.from(received);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

// Best-effort per-instance protection. The access token remains the primary gate.
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

export async function POST(request) {
  const apiKey = process.env.OPENAI_API_KEY;
  const accessToken = process.env.YELLOW_CHAT_ACCESS_TOKEN;

  if (!apiKey || !accessToken) {
    return json({ ok: false, error: "chat_not_configured" }, 503);
  }

  const incomingToken = request.headers.get("x-yellow-chat-token") || "";
  if (!safeEqual(incomingToken, accessToken)) {
    return json({ ok: false, error: "unauthorized" }, 401);
  }

  // Vercel provides x-forwarded-for; use only the first address for a light throttle.
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
    upstream = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + apiKey,
        "Content-Type": "application/json"
      },
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
      body: JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-5-mini",
        instructions: "You are a helpful, honest assistant. Reply in the language used by the user. Be clear and accurate. Do not claim to have performed actions you have not performed.",
        input: messages,
        max_output_tokens: 1400,
        store: false
      })
    });
  } catch {
    return json({ ok: false, error: "provider_error" }, 502);
  }

  const raw = await upstream.text();
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return json({ ok: false, error: "provider_error" }, 502);
  }

  if (!upstream.ok || data?.error) {
    return json({ ok: false, error: "provider_error", status: upstream.status }, 502);
  }

  const text = typeof data.output_text === "string"
    ? data.output_text.trim()
    : (data.output || [])
        .filter(item => item?.type === "message")
        .flatMap(item => item.content || [])
        .filter(item => item?.type === "output_text" && typeof item.text === "string")
        .map(item => item.text)
        .join("\n")
        .trim();

  if (!text) return json({ ok: false, error: "provider_error" }, 502);
  return json({ ok: true, text });
}
