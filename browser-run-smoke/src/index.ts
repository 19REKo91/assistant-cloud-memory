import puppeteer from "@cloudflare/puppeteer";

interface Env {
  BROWSER: any;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Fixed, read-only smoke test. No arbitrary target URL or public control API.
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

      const anchors = await page.$$("a");
      const firstLink = anchors.length
        ? await page.$eval("a", (element: Element) => element.textContent?.trim() || null).catch(() => null)
        : null;

      return Response.json({
        ok: true,
        engine: "Cloudflare Browser Run via Puppeteer",
        status: response?.status() ?? null,
        url: page.url(),
        title: await page.title(),
        links: anchors.length,
        firstLink
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
