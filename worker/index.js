// phish-proxy-worker.js — Cloudflare Worker
// Proxies phish.in v2 API (no auth required) with CORS headers

export default {
  async fetch(request) {
    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405 });
    }

    const url = new URL(request.url);
    // Route: /shows/YYYY-MM-DD  or  /search/term
    const showMatch   = url.pathname.match(/\/shows\/(\d{4}-\d{2}-\d{2})/);
    const searchMatch = url.pathname.match(/\/search\/(.+)/);

    let phishInUrl;
    if (showMatch) {
      phishInUrl = `https://phish.in/api/v2/shows/${showMatch[1]}`;
    } else if (searchMatch) {
      phishInUrl = `https://phish.in/api/v2/search/${searchMatch[1]}`;
    } else {
      return new Response('Usage: /shows/YYYY-MM-DD or /search/term', { status: 400 });
    }

    try {
      const response = await fetch(phishInUrl, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'dial-a-phish/1.0',
        }
      });

      const body = await response.text();

      return new Response(body, {
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET',
          'Cache-Control': 'public, max-age=3600',
        }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), {
        status: 502,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        }
      });
    }
  }
};
