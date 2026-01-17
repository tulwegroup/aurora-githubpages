import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

console.log(`🚀 Starting Aurora OSI Frontend Server`);
console.log(`📍 Port: ${PORT}`);
console.log(`🔗 Backend URL: ${BACKEND_URL}`);

// Wrap startup in async IIFE to allow async operations
(async () => {
  // Test backend connectivity on startup
  try {
    const response = await fetch(`${BACKEND_URL}/health`, { timeout: 5000 });
    if (response.ok) {
      console.log(`✓ Backend service is reachable at ${BACKEND_URL}`);
    } else {
      console.warn(`⚠️ Backend service returned ${response.status}`);
    }
  } catch (err) {
    console.warn(`⚠️ Backend service unreachable at ${BACKEND_URL}: ${err.message}`);
    console.warn(`   Frontend will run, but API calls may fail. Configure BACKEND_URL environment variable.`);
  }
})();

// Proxy API calls to backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': ''
  },
  onError: (err, req, res) => {
    console.error(`❌ Proxy error for ${req.path}:`, err.message);
    res.status(503).json({ 
      error: 'Backend service unavailable',
      details: `Could not reach backend at ${BACKEND_URL}`,
      suggestion: `Set BACKEND_URL environment variable to your backend service URL`
    });
  },
  onProxyRes: (proxyRes, req, res) => {
    proxyRes.headers['X-Proxied-By'] = 'Aurora Frontend';
  }
}));

// Serve static files from dist
app.use(express.static(path.join(__dirname, 'dist')));

// SPA fallback - serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✓ Server running on http://0.0.0.0:${PORT}`);
});
