# Multi-stage build: Node.js frontend + Python backend
FROM node:22-alpine AS frontend-build

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Use proven tiangolo image built for FastAPI + uvicorn
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

# Install Node.js for frontend serving
RUN apt-get update && apt-get install -y \
    curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install frontend dependencies
COPY package.json ./
RUN npm install --omit=prod

# Copy built frontend dist
COPY --from=frontend-build /app/dist ./dist

# Copy backend source code
COPY backend ./backend
COPY . .

# Copy app_wrapper as the main app
COPY app_wrapper.py /app/main.py

# The tiangolo image automatically handles uvicorn startup
# It looks for /app/main.py by default and runs it
ENV APP_MODULE=main:app
ENV LOG_LEVEL=info
