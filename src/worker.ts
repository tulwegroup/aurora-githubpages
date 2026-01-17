import { getAssetFromKV, NotFoundError, MethodNotAllowedError } from '@cloudflare/kv-asset-handler';

type Env = {
  __STATIC_CONTENT: KVNamespace;
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      return await getAssetFromKV(
        {
          request,
          waitUntil: (promise: Promise<any>) => {},
        } as any,
        {
          ASSET_NAMESPACE: env.__STATIC_CONTENT,
          ASSET_MANIFEST: __STATIC_CONTENT_MANIFEST,
        } as any
      );
    } catch (e: any) {
      // Handle SPA routing - return index.html for any route that's not a static asset
      if (e instanceof NotFoundError) {
        try {
          return await getAssetFromKV(
            {
              request: new Request(`${new URL(request.url).origin}/index.html`, request),
              waitUntil: (promise: Promise<any>) => {},
            } as any,
            {
              ASSET_NAMESPACE: env.__STATIC_CONTENT,
              ASSET_MANIFEST: __STATIC_CONTENT_MANIFEST,
            } as any
          );
        } catch (e2) {
          return new Response('Not Found', { status: 404 });
        }
      } else if (e instanceof MethodNotAllowedError) {
        return new Response('Method Not Allowed', { status: 405 });
      }
      return new Response('Internal Server Error', { status: 500 });
    }
  },
} as ExportedHandler<Env>;

declare const __STATIC_CONTENT_MANIFEST: string;
