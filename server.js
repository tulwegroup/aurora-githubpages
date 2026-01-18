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

// Try to read and display backend logs
const fs = require('fs');
try {
  const logs = fs.readFileSync('/tmp/backend.log', 'utf8').split('\n').slice(-10);
  console.log(`\n📋 Last 10 lines of backend log:`);
  logs.forEach(line => line && console.log(`   ${line}`));
  console.log('');
} catch (e) {
  console.log('(Backend log not yet available)\n');
}

// Wrap startup in async IIFE to allow async operations
(async () => {
  // Test backend connectivity on startup with retries
  // This is informational only - don't fail if backend isn't ready yet
  let backendReady = false;
  let attempts = 0;
  const maxAttempts = 20;
  
  console.log(`\n📡 Attempting to verify backend connectivity...`);
  while (!backendReady && attempts < maxAttempts) {
    try {
      attempts++;
      const response = await fetch(`${BACKEND_URL}/health`, { 
        timeout: 2000,
        signal: AbortSignal.timeout(2000)
      });
      if (response.ok) {
        console.log(`✅ Backend service is reachable at ${BACKEND_URL}`);
        backendReady = true;
      }
    } catch (err) {
      if (attempts % 5 === 0) {
        console.log(`⏳ Backend still initializing (attempt ${attempts}/${maxAttempts})...`);
      }
      if (attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 1000));
      }
    }
  }
  
  if (!backendReady) {
    console.warn(`\n⚠️  Backend not responding yet at ${BACKEND_URL}`);
    console.warn(`   API calls will use the proxy - retries will happen automatically\n`);
  }
  
  // Don't block - Express will handle backend connectivity issues with automatic retries
})();

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
