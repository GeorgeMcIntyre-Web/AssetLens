const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

function targetUrl(path: string): string {
  const base = API_BASE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

function forwardHeaders(req: Request): Headers {
  const h = new Headers(req.headers);
  h.delete('host');
  return h;
}

async function proxy(req: Request, ctx: { params: Promise<{ path: string[] }> }): Promise<Response> {
  const { path } = await ctx.params;
  const tail = `/${path.join('/')}`;

  const url = new URL(req.url);
  const target = targetUrl(`${tail}${url.search}`);

  const init: RequestInit = {
    method: req.method,
    headers: forwardHeaders(req),
  };

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = req.body;
    // Required when streaming a body via fetch() on Node.
    // @ts-expect-error - duplex is supported by undici
    init.duplex = 'half';
  }

  const upstream = await fetch(target, init);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: upstream.headers,
  });
}

export async function GET(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, ctx);
}

export async function POST(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, ctx);
}

export async function PUT(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, ctx);
}

export async function DELETE(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  return proxy(req, ctx);
}
