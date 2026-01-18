FROM node:18-alpine

WORKDIR /app

# Install Python, build tools, and dependencies
RUN apk add --no-cache python3 py3-pip py3-psycopg2 gcc python3-dev musl-dev linux-headers

# Copy backend requirements
COPY backend/requirements.txt ./backend/

# Install Python dependencies (use --break-system-packages for Alpine)
# Use verbose output and fail on error
RUN pip3 install --no-cache-dir --break-system-packages --require-hashes=no -r ./backend/requirements.txt && \
    echo "✓ Python dependencies installed" && \
    python3 -m pip list | grep -E "sqlalchemy|apscheduler|psutil" || (echo "❌ Missing critical packages!" && exit 1)

# Clean up build tools to reduce image size
RUN apk del gcc python3-dev musl-dev linux-headers

# Copy package files for Node
COPY package*.json ./

# Install Node dependencies
RUN npm install && npm install --save express http-proxy-middleware

# Copy entire application
COPY . .

# Build frontend
RUN npm run build

# Expose ports
EXPOSE 3000 8000

# Health check for frontend
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Create startup script with backend startup
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo 'echo "Starting Aurora OSI services..."' >> /app/start.sh && \
    echo 'export BACKEND_URL=${BACKEND_URL:-http://localhost:8000}' >> /app/start.sh && \
    echo 'echo "Backend URL: $BACKEND_URL"' >> /app/start.sh && \
    echo 'echo "Starting FastAPI backend on port 8000..."' >> /app/start.sh && \
    echo 'python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info > /tmp/backend.log 2>&1 &' >> /app/start.sh && \
    echo 'BACKEND_PID=$!' >> /app/start.sh && \
    echo 'echo "Backend PID: $BACKEND_PID"' >> /app/start.sh && \
    echo 'sleep 5' >> /app/start.sh && \
    echo 'if ! kill -0 $BACKEND_PID 2>/dev/null; then' >> /app/start.sh && \
    echo '  echo "❌ Backend process crashed! Logs:"' >> /app/start.sh && \
    echo '  cat /tmp/backend.log' >> /app/start.sh && \
    echo '  exit 1' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo 'echo "✓ Backend process running (PID: $BACKEND_PID)"' >> /app/start.sh && \
    echo 'echo "Starting Express frontend on port 3000..."' >> /app/start.sh && \
    echo 'node server.js' >> /app/start.sh && \
    chmod +x /app/start.sh

# Start both services
CMD ["/bin/sh", "/app/start.sh"]
