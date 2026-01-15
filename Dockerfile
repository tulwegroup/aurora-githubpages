# Multi-stage build: Node.js frontend + Python backend
FROM node:22-alpine AS frontend-build

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Use Python base, NOT tiangolo (too much magic)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install frontend deps
COPY package.json ./
RUN npm install --omit=dev

# Copy built frontend
COPY --from=frontend-build /app/dist ./dist

# Copy backend and app files
COPY backend ./backend
COPY . .
COPY app_wrapper.py ./main.py

# Unbuffered Python output
ENV PYTHONUNBUFFERED=1

# CRITICAL: Expose port so Railway knows
EXPOSE 8000

# Start the app - simple and direct
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
