export interface Env {
  GEMINI_API_KEY: string;
  BRIDGE_TOKEN?: string;
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") return json({ ok: true, service: "vision-bridge", usage: "POST {image_url,prompt}" });

    if (env.BRIDGE_TOKEN) {
      const supplied = request.headers.get("x-bridge-token");
      if (supplied !== env.BRIDGE_TOKEN) return json({ error: "unauthorized" }, 401);
    }

    let body: any;
    try { body = await request.json(); } catch { return json({ error: "invalid_json" }, 400); }

    const imageUrl = typeof body?.image_url === "string" ? body.image_url : "";
    const prompt = typeof body?.prompt === "string" && body.prompt.trim()
      ? body.prompt
      : "Describe the image accurately. Return concise text only. Do not reproduce the image.";

    if (!/^https?:\/\//i.test(imageUrl)) return json({ error: "image_url_required" }, 400);
    if (!env.GEMINI_API_KEY) return json({ error: "GEMINI_API_KEY_not_configured" }, 503);

    const upstream = await fetch("https://generativelanguage.googleapis.com/v1beta/interactions", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-goog-api-key": env.GEMINI_API_KEY,
      },
      body: JSON.stringify({
        model: "gemini-3.8-flash",
        input: [
          { type: "text", text: prompt },
          { type: "image", uri: imageUrl, mime_type: "image/jpeg" }
        ],
        response_format: { type: "text" }
      }),
    });

    const raw = await upstream.text();
    if (!upstream.ok) return json({ error: "gemini_error", status: upstream.status, detail: raw.slice(0, 1000) }, 502);

    let data: any;
    try { data = JSON.parse(raw); } catch { return json({ error: "gemini_invalid_response" }, 502); }

    const text =
      data?.outputText ??
      data?.output?.find?.((x: any) => typeof x?.text === "string")?.text ??
      data?.response?.text ??
      "";

    return json({ ok: true, text: typeof text === "string" ? text : String(text) });
  }
} satisfies ExportedHandler<Env>;
