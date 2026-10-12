import puppeteer from "@cloudflare/puppeteer";

interface Env {
  BROWSER: any;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // A deliberately fixed, read-only smoke test. It accepts no target URL
    // and exposes no arbitrary browser-control endpoint.
    if (request.method !== "GET" || url.pathname !== "/smoke") {
      return new Response("Not found", { status: 404 });
    }

    let browser: any;
    try {
      browser = await puppeteer.launch(env.BROWSER);
      const page = await browser.newPage();
      const response = await page.goto("https://example.com", {
        waitUntil: "domcontentloaded",
        timeout: 20000
      });

      return Response.json({
        ok: true,
        engine: "Cloudflare Browser Run via Puppeteer",
        status: response?.status() ?? null,
        url: page.url(),
        title: await page.title(),
        links: await page.locator("a").count(),
        firstLink: await page.locator("a").first().innerText().catch(() => null)
      }, {
        headers: { "cache-control": "no-store" }
      });
    } catch (error) {
      return Response.json({
        ok: false,
        engine: "Cloudflare Browser Run via Puppeteer",
        error: String(error)
      }, { status: 500 });
    } finally {
      if (browser) await browser.close().catch(() => undefined);
    }
  }
};
