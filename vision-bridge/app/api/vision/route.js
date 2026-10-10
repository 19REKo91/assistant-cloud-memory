import { head } from "@vercel/blob";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEFAULT_PROMPT =
  "Describe the visible screen accurately. Read visible text when possible. Return concise text only.";

export async function POST(request) {
  let body = {};
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "invalid_json" }, { status: 400 });
  }

  const prompt =
    typeof body?.prompt === "string" && body.prompt.trim()
      ? body.prompt.trim().slice(0, 2000)
      : DEFAULT_PROMPT;

  let frame;
  try {
    frame = await head("latest-frame.png");
  } catch {
    return Response.json(
      { error: "no_frame_yet", message: "ارفع صورة أولاً ثم أعد التحليل." },
      { status: 404, headers: { "Cache-Control": "no-store" } }
    );
  }

  const workerEndpoint =
    process.env.VISION_BRIDGE_WORKER_URL ||
    "https://chatgpt-vision-bridge.flourish-gerbil.workers.dev/vision";

  let workerUrl;
  try {
    workerUrl = new URL(workerEndpoint);
  } catch {
    return Response.json({ error: "invalid_worker_url" }, { status: 500 });
  }

  workerUrl.searchParams.set("image_url", frame.url);
  workerUrl.searchParams.set("prompt", prompt);

  if (process.env.VISION_BRIDGE_TOKEN) {
    workerUrl.searchParams.set("token", process.env.VISION_BRIDGE_TOKEN);
  }

  let upstream;
  try {
    upstream = await fetch(workerUrl, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(90000)
    });
  } catch (error) {
    return Response.json(
      {
        error: "vision_worker_unreachable",
        detail: error instanceof Error ? error.message : "unknown_error"
      },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }

  const raw = await upstream.text();
  let result;
  try {
    result = JSON.parse(raw);
  } catch {
    return Response.json(
      { error: "invalid_worker_response", status: upstream.status, detail: raw.slice(0, 500) },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }

  if (!upstream.ok || result?.error) {
    return Response.json(
      {
        error: result?.error || "vision_analysis_failed",
        status: upstream.status,
        detail: result?.detail || result?.message || undefined
      },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }

  return Response.json(
    { ok: true, text: typeof result?.text === "string" ? result.text : "", frame_url: frame.url },
    { headers: { "Cache-Control": "no-store" } }
  );
}
