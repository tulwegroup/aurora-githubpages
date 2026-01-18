import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

console.log(`🚀 Starting Aurora OSI Frontend Server`);
console.log(`📍 Port: ${PORT}`);
console.log(`🔗 Backend URL: ${BACKEND_URL}`);

// Try to read and display backend logs for diagnostic purposes
try {
  const logs = fs.readFileSync('/tmp/backend.log', 'utf8').split('\n').slice(-5).filter(line => line.trim());
  if (logs.length > 0) {
    console.log(`\n📋 Recent backend log:\n${logs.map(l => '   ' + l).join('\n')}\n`);
  }
} catch (e) {
  // Backend logs not available yet
}

console.log(`\n🔗 Express proxy routing /api → ${BACKEND_URL}`);
console.log(`📡 Backend connectivity check skipped (proxy will retry automatically)\n`);

// Proxy API calls to backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': ''
  },
  logLevel: 'debug',
  timeout: 30000,
  proxyTimeout: 30000,
  onError: (err, req, res) => {
    console.error(`❌ Proxy error for ${req.method} ${req.path}:`, err.message);
    res.status(503).json({ 
      error: 'Backend service unavailable',
      details: `Could not reach backend at ${BACKEND_URL}`,
      hint: `Check if backend is running at ${BACKEND_URL} or set BACKEND_URL environment variable`,
      originalError: err.message,
      path: req.path
    });
  },
  onProxyRes: (proxyRes, req, res) => {
    proxyRes.headers['X-Proxied-By'] = 'Aurora Frontend';
    proxyRes.headers['X-Backend-URL'] = BACKEND_URL;
  }
}));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', backend: BACKEND_URL, timestamp: new Date().toISOString() });
});

// Serve static files from dist
app.use(express.static(path.join(__dirname, 'dist')));

// SPA fallback - serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✓ Server running on http://0.0.0.0:${PORT}`);
});
