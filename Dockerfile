FROM node:18-alpine

WORKDIR /app

# Install Python, build tools, and dependencies
RUN apk add --no-cache python3 py3-pip py3-psycopg2 gcc python3-dev musl-dev linux-headers netcat-openbsd wget

# Copy backend requirements
COPY backend/requirements.txt ./backend/

# Install Python dependencies (use --break-system-packages for Alpine)
# Use verbose output and fail on error
RUN pip3 install --no-cache-dir --break-system-packages -r ./backend/requirements.txt && \
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
    echo 'python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info 2>&1 | tee /tmp/backend.log &' >> /app/start.sh && \
    echo 'BACKEND_PID=$!' >> /app/start.sh && \
    echo 'echo "Backend PID: $BACKEND_PID"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Wait and verify backend is listening' >> /app/start.sh && \
    echo 'MAX_ATTEMPTS=20' >> /app/start.sh && \
    echo 'ATTEMPT=0' >> /app/start.sh && \
    echo 'while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do' >> /app/start.sh && \
    echo '  sleep 1' >> /app/start.sh && \
    echo '  ATTEMPT=$((ATTEMPT + 1))' >> /app/start.sh && \
    echo '  if ! kill -0 $BACKEND_PID 2>/dev/null; then' >> /app/start.sh && \
    echo '    echo "❌ Backend process crashed after $ATTEMPT seconds!"' >> /app/start.sh && \
    echo '    echo "=== Backend Error Logs ===" >> /app/start.sh && \
    echo '    cat /tmp/backend.log' >> /app/start.sh && \
    echo '    exit 1' >> /app/start.sh && \
    echo '  fi' >> /app/start.sh && \
    echo '  if nc -z localhost 8000 2>/dev/null || wget --quiet --tries=1 http://localhost:8000/health 2>/dev/null; then' >> /app/start.sh && \
    echo '    echo "✅ Backend is listening on port 8000"' >> /app/start.sh && \
    echo '    break' >> /app/start.sh && \
    echo '  fi' >> /app/start.sh && \
    echo '  if [ $ATTEMPT -eq 5 ] || [ $ATTEMPT -eq 10 ] || [ $ATTEMPT -eq 15 ]; then' >> /app/start.sh && \
    echo '    echo "⏳ Still waiting for backend... (attempt $ATTEMPT/$MAX_ATTEMPTS)"' >> /app/start.sh && \
    echo '  fi' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then' >> /app/start.sh && \
    echo '  echo "❌ Backend failed to start listening after $MAX_ATTEMPTS attempts"' >> /app/start.sh && \
    echo '  echo "=== Last 20 lines of backend log ===" >> /app/start.sh && \
    echo '  tail -20 /tmp/backend.log' >> /app/start.sh && \
    echo '  kill $BACKEND_PID 2>/dev/null || true' >> /app/start.sh && \
    echo '  exit 1' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "Starting Express frontend on port 3000..."' >> /app/start.sh && \
    echo 'node server.js' >> /app/start.sh && \
    chmod +x /app/start.sh

# Start both services
CMD ["/bin/sh", "/app/start.sh"]
