# Multi-stage build: Node.js frontend + Python backend
FROM node:22-alpine AS frontend-build

WORKDIR /app

# Copy frontend dependencies and source
COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# Final runtime image: Python + Node.js
FROM python:3.11-slim

WORKDIR /app

# Install Node.js in Python image
RUN apt-get update && apt-get install -y \
    curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy npm modules from frontend build
COPY package.json ./
RUN npm install --omit=prod

# Copy built frontend dist
COPY --from=frontend-build /app/dist ./dist

# Copy backend source code
COPY backend ./backend
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=true
ENV PORT=8000
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port for Railway
EXPOSE 8000

# Health check - call /system/health endpoint directly
HEALTHCHECK --interval=10s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/system/health || exit 1

# Start with uvicorn app_wrapper with verbose logging
CMD ["sh", "-c", "echo 'Starting Aurora OSI v3 on port 8000' && uvicorn app_wrapper:app --host 0.0.0.0 --port 8000 --log-level debug"]
