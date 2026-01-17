export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);
    
    // Let Cloudflare Pages handle static assets (js, css, images, etc)
    // Only intercept routes for SPA
    if (!url.pathname.includes('.') && !url.pathname.startsWith('/api')) {
      // For SPA routes without file extensions, serve index.html
      const indexResponse = await fetch(new Request(new URL('/index.html', url).toString(), {
        method: request.method,
        headers: request.headers,
      }));
      
      if (indexResponse.ok) {
        return indexResponse;
      }
    }
    
    // For everything else, let Cloudflare Pages handle it
    return fetch(request);
  },
};

