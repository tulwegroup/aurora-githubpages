FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Build frontend
COPY . .
RUN npm run build

# Install express for simple server
RUN npm install --save express http-proxy-middleware

# Create server file
RUN cat > server.js << 'EOF'
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Proxy API calls to backend
app.use('/api', createProxyMiddleware({
  target: process.env.BACKEND_URL || 'http://localhost:8000',
  changeOrigin: true,
  pathRewrite: {
    '^/api': ''
  }
}));

// Serve static files
app.use(express.static(path.join(__dirname, 'dist')));

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

EXPOSE 3000

CMD ["node", "server.js"]
