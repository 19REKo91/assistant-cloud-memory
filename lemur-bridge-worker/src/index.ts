const COMMAND_URL =
  "https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/lemur-browser-command-poc/SYNC/LEMUR_COMMAND.json";
const ALLOWED_HOSTS = new Set(["example.com", "www.iana.org"]);

interface Env {
  RESULTS: DurableObjectNamespace;
}

type LemurResult = {
  id: string;
  action: "navigate";
  requestedUrl: string;
  actualUrl: string;
  title: string;
  completedAt: string;
  source: "lemur-extension-poc";
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET,POST,OPTIONS",
      "access-control-allow-headers": "content-type"
    }
  });
}

function allowedUrl(value: unknown): URL | null {
  if (typeof value !== "string" || value.length > 1500) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || !ALLOWED_HOSTS.has(url.hostname)) return null;
    if (url.hostname === "example.com" && url.pathname !== "/") return null;
    if (url.hostname === "www.iana.org" && url.pathname !== "/help/example-domains") return null;
    return url;
  } catch {
    return null;
  }
}

async function getCurrentCommand(): Promise<any | null> {
  try {
    const response = await fetch(COMMAND_URL + "?_=" + Date.now(), {
      cache: "no-store",
      headers: { accept: "application/json" }
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return json({}, 204);

    if (request.method === "GET" && url.pathname === "/health") {
      return json({
        ok: true,
        service: "lemur-browser-bridge-poc",
        mode: "metadata-only",
        allowedHosts: [...ALLOWED_HOSTS]
      });
    }

    if (request.method === "POST" && url.pathname === "/result") {
      const raw = await request.text();
      if (raw.length > 4000) return json({ ok: false, error: "payload_too_large" }, 413);
      let result: LemurResult;
      try {
        result = JSON.parse(raw);
      } catch {
        return json({ ok: false, error: "invalid_json" }, 400);
      }

      if (
        !result ||
        typeof result.id !== "string" ||
        !/^[a-zA-Z0-9_-]{8,100}$/.test(result.id) ||
        result.action !== "navigate" ||
        result.source !== "lemur-extension-poc" ||
        typeof result.title !== "string" ||
        result.title.length > 180 ||
        typeof result.completedAt !== "string"
      ) {
        return json({ ok: false, error: "invalid_result" }, 400);
      }

      const command = await getCurrentCommand();
      if (!command || command.version !== 1 || command.id !== result.id || command.action !== "navigate") {
        return json({ ok: false, error: "command_id_mismatch" }, 409);
      }

      const requested = allowedUrl(command.url);
      const requestedFromResult = allowedUrl(result.requestedUrl);
      const actual = allowedUrl(result.actualUrl);
      if (
        !requested ||
        !requestedFromResult ||
        !actual ||
        requested.href !== requestedFromResult.href ||
        requested.origin !== actual.origin
      ) {
        return json({ ok: false, error: "url_not_allowed" }, 400);
      }

      const objectId = env.RESULTS.idFromName(result.id);
      const object = env.RESULTS.get(objectId);
      return object.fetch("https://result-store.local/store", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ...result,
          actualUrl: actual.origin + actual.pathname,
          title: result.title.trim()
        })
      });
    }

    const match = request.method === "GET" && url.pathname.match(/^\/result\/([a-zA-Z0-9_-]{8,100})$/);
    if (match) {
      const objectId = env.RESULTS.idFromName(match[1]);
      const object = env.RESULTS.get(objectId);
      return object.fetch("https://result-store.local/read");
    }

    return json({ ok: false, error: "not_found" }, 404);
  }
};

export class ResultStore {
  constructor(private readonly ctx: DurableObjectState) {}

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/store") {
      const existing = await this.ctx.storage.get<LemurResult>("result");
      if (existing) return json({ ok: false, error: "result_already_recorded" }, 409);
      let result: LemurResult;
      try {
        result = await request.json();
      } catch {
        return json({ ok: false, error: "invalid_json" }, 400);
      }
      await this.ctx.storage.put("result", result);
      return json({ ok: true, id: result.id });
    }

    if (request.method === "GET" && url.pathname === "/read") {
      const result = await this.ctx.storage.get<LemurResult>("result");
      return result ? json({ ok: true, result }) : json({ ok: false, error: "result_not_ready" }, 404);
    }

    return json({ ok: false, error: "not_found" }, 404);
  }
}
