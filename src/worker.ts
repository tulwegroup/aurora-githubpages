export default {
  async fetch(request: Request, env: any): Promise<Response> {
    const url = new URL(request.url);
    
    // Handle static assets
    if (url.pathname.match(/\.(js|css|png|jpg|gif|svg|woff|woff2|ttf|eot|ico)$/)) {
      try {
        const response = await env.__STATIC_CONTENT.get(url.pathname.substring(1), {
          type: 'arrayBuffer',
        });
        
        if (!response) {
          return new Response('Not Found', { status: 404 });
        }

        const contentType = getContentType(url.pathname);
        return new Response(response, {
          headers: {
            'Content-Type': contentType,
            'Cache-Control': 'public, max-age=3600',
          },
        });
      } catch (e) {
        return new Response('Not Found', { status: 404 });
      }
    }

    // Serve index.html for SPA routing
    try {
      const indexContent = await env.__STATIC_CONTENT.get('index.html', {
        type: 'text',
      });

      if (!indexContent) {
        return new Response('Not Found', { status: 404 });
      }

      return new Response(indexContent, {
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      });
    } catch (e) {
      return new Response('Internal Server Error', { status: 500 });
    }
  },
};

function getContentType(pathname: string): string {
  const ext = pathname.split('.').pop()?.toLowerCase();
  const mimeTypes: Record<string, string> = {
    'js': 'application/javascript',
    'css': 'text/css',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'eot': 'application/vnd.ms-fontobject',
    'ico': 'image/x-icon',
    'json': 'application/json',
    'html': 'text/html',
  };
  return mimeTypes[ext || ''] || 'application/octet-stream';
}
