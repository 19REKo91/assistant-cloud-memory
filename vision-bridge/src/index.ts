export interface Env {
  GEMINI_API_KEY: string;
  BRIDGE_TOKEN?: string;
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type,x-bridge-token"
    }
  });
}

const DEFAULT_PROMPT =
  "Describe the image accurately. Return concise text only. Do not reproduce the image.";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Text-only vision gateway:
    // The worker fetches the image and Gemini sees it.
    // ChatGPT only receives compact JSON text, not image bytes.
    if (request.method === "GET" && url.pathname === "/vision") {
      const imageUrl = url.searchParams.get("image_url") || "";
      const prompt = url.searchParams.get("prompt")?.trim() || DEFAULT_PROMPT;
      const token = url.searchParams.get("token") || "";

      if (env.BRIDGE_TOKEN && token !== env.BRIDGE_TOKEN) {
        return json({ error: "unauthorized" }, 401);
      }

      if (!/^https?:\/\//i.test(imageUrl)) {
        return json({ error: "image_url_required" }, 400);
      }

      return analyzeRemoteImage(env, imageUrl, prompt);
    }

    if (request.method === "OPTIONS") return new Response(null, {
      status: 204,
      headers: {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "access-control-allow-headers": "content-type,x-bridge-token"
      }
    });

    if (request.method !== "POST") return json({
      ok: true,
      service: "vision-bridge",
      usage:
        "GET /vision?image_url=<url>&prompt=<question> OR POST /vision {image_base64,mime_type,prompt}"
    });

    if (env.BRIDGE_TOKEN && request.headers.get("x-bridge-token") !== env.BRIDGE_TOKEN) {
      return json({ error: "unauthorized" }, 401);
    }

    let body: any;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid_json" }, 400);
    }

    const prompt = typeof body?.prompt === "string" && body.prompt.trim()
      ? body.prompt
      : DEFAULT_PROMPT;

    let contentType = typeof body?.mime_type === "string"
      ? body.mime_type
      : "image/jpeg";

    let imageBase64 = typeof body?.image_base64 === "string"
      ? body.image_base64
      : "";

    if (!imageBase64 && typeof body?.image_url === "string" && /^https?:\/\//i.test(body.image_url)) {
      return analyzeRemoteImage(env, body.image_url, prompt);
    }

    if (!imageBase64) return json({
      error: "image_base64_required"
    }, 400);

    if (!contentType.toLowerCase().startsWith("image/")) {
      return json({ error: "not_an_image" }, 415);
    }

    if (Math.floor(imageBase64.length * 0.75) > 20 * 1024 * 1024) {
      return json({ error: "image_too_large" }, 413);
    }

    return analyzeBase64Image(env, imageBase64, contentType, prompt);
  }
} satisfies ExportedHandler<Env>;

async function analyzeRemoteImage(
  env: Env,
  imageUrl: string,
  prompt: string
): Promise<Response> {
  let imageResponse: Response;

  try {
    imageResponse = await fetch(imageUrl, {
      redirect: "follow",
      headers: { "accept": "image/*,*/*;q=0.8" }
    });
  } catch {
    return json({ error: "image_fetch_failed" }, 502);
  }

  if (!imageResponse.ok) {
    return json({
      error: "image_fetch_failed",
      status: imageResponse.status
    }, 502);
  }

  const contentType = imageResponse.headers.get("content-type") || "image/jpeg";

  if (!contentType.toLowerCase().startsWith("image/")) {
    return json({
      error: "not_an_image",
      content_type: contentType
    }, 415);
  }

  const raw = new Uint8Array(await imageResponse.arrayBuffer());

  if (raw.byteLength > 20 * 1024 * 1024) {
    return json({ error: "image_too_large" }, 413);
  }

  return analyzeBase64Image(
    env,
    uint8ToBase64(raw),
    contentType.split(";")[0],
    prompt
  );
}

async function analyzeBase64Image(
  env: Env,
  imageBase64: string,
  contentType: string,
  prompt: string
): Promise<Response> {
  if (!env.GEMINI_API_KEY) {
    return json({ error: "GEMINI_API_KEY_not_configured" }, 503);
  }

  const payload = JSON.stringify({
    contents: [{
      parts: [
        {
          inline_data: {
            mime_type: contentType.split(";")[0],
            data: imageBase64
          }
        },
        { text: prompt }
      ]
    }]
  });

  let raw = "";
  let upstreamStatus = 0;

  for (let attempt = 1; attempt <= 3; attempt++) {
    const upstream = await fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-goog-api-key": env.GEMINI_API_KEY
        },
        body: payload
      }
    );

    upstreamStatus = upstream.status;
    raw = await upstream.text();

    if (upstream.ok) break;

    if (![429, 500, 502, 503, 504].includes(upstream.status) || attempt === 3) {
      return json({
        error: "gemini_error",
        status: upstream.status,
        detail: raw.slice(0, 1000)
      }, 502);
    }

    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
  }

  let data: any;

  try {
    data = JSON.parse(raw);
  } catch {
    return json({
      error: "gemini_invalid_response",
      status: upstreamStatus
    }, 502);
  }

  const text = data?.candidates?.[0]?.content?.parts
    ?.filter((p: any) => typeof p?.text === "string")
    ?.map((p: any) => p.text)
    ?.join("\n")
    ?.trim() || "";

  return json({
    ok: true,
    text
  });
}

function uint8ToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunk = 0x8000;

  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(
      ...bytes.subarray(i, Math.min(i + chunk, bytes.length))
    );
  }

  return btoa(binary);
}
