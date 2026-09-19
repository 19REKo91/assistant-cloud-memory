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

    // Fetch the image on the Worker side. The image bytes never enter ChatGPT.
    const imageResponse = await fetch(imageUrl);
    if (!imageResponse.ok) {
      return json({ error: "image_fetch_failed", status: imageResponse.status }, 502);
    }

    const contentType = imageResponse.headers.get("content-type") || "image/jpeg";
    if (!contentType.toLowerCase().startsWith("image/")) {
      return json({ error: "not_an_image", content_type: contentType }, 415);
    }

    const imageBytes = new Uint8Array(await imageResponse.arrayBuffer());
    if (imageBytes.byteLength > 20 * 1024 * 1024) {
      return json({ error: "image_too_large" }, 413);
    }

    // Gemini GenerateContent: image bytes are sent from Worker directly to Gemini.
    const upstream = await fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-goog-api-key": env.GEMINI_API_KEY,
        },
        body: JSON.stringify({
          contents: [{
            parts: [
              {
                inline_data: {
                  mime_type: contentType.split(";")[0],
                  data: uint8ToBase64(imageBytes),
                },
              },
              { text: prompt },
            ],
          }],
        }),
      },
    );

    const raw = await upstream.text();
    if (!upstream.ok) {
      return json({ error: "gemini_error", status: upstream.status, detail: raw.slice(0, 1000) }, 502);
    }

    let data: any;
    try { data = JSON.parse(raw); } catch { return json({ error: "gemini_invalid_response" }, 502); }

    const text = data?.candidates?.[0]?.content?.parts
      ?.filter((p: any) => typeof p?.text === "string")
      ?.map((p: any) => p.text)
      ?.join("\n")
      ?.trim() || "";

    return json({ ok: true, text });
  }
} satisfies ExportedHandler<Env>;

function uint8ToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + chunk, bytes.length)));
  }
  return btoa(binary);
}
