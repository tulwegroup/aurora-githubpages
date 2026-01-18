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
COPY <<EOF /app/container-start.sh
#!/bin/sh
set -e
echo "Starting Aurora OSI services..."
export BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
echo "Backend URL: $BACKEND_URL"
echo "Starting FastAPI backend on port 8000..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info 2>&1 | tee /tmp/backend.log &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait and verify backend is listening
MAX_ATTEMPTS=20
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 1
  ATTEMPT=$((ATTEMPT + 1))
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend process crashed after $ATTEMPT seconds!"
    cat /tmp/backend.log
    exit 1
  fi
  if nc -z localhost 8000 2>/dev/null || wget --quiet --tries=1 http://localhost:8000/health 2>/dev/null; then
    echo "✅ Backend is listening on port 8000"
    break
  fi
  if [ $ATTEMPT -eq 5 ] || [ $ATTEMPT -eq 10 ] || [ $ATTEMPT -eq 15 ]; then
    echo "⏳ Still waiting for backend... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
  fi
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
  echo "❌ Backend failed to start listening after $MAX_ATTEMPTS attempts"
  tail -20 /tmp/backend.log
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

echo "Starting Express frontend..."
node server.js
EOF

RUN chmod +x /app/container-start.sh

# Start both services
CMD ["/bin/sh", "/app/container-start.sh"]
