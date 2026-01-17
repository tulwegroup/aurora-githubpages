FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn

# Frontend builder
FROM node:18-alpine as frontend-builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Final runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client curl nginx && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy backend code
COPY backend ./backend
COPY app_wrapper.py ./main.py

# Copy frontend build
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Configure nginx to proxy API requests to backend
RUN echo 'server { \
    listen 80; \
    server_name _; \
    location / { \
        root /usr/share/nginx/html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://localhost:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Start both nginx and backend
CMD bash -c "nginx -g \"daemon off;\" & \
    gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    backend.main:app"
