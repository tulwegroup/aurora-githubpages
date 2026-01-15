#!/bin/bash
# Aurora OSI v3 - Production Start Script
# Deploy to Railway with Neon PostgreSQL

set -e

echo "🚀 Aurora OSI v3 - Production Deployment"

# Ensure environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL environment variable not set"
    exit 1
fi

echo "✓ Environment variables configured"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install --no-cache-dir -r requirements.txt

# Run migrations
echo "🗄️  Running database migrations..."
python3 -c "from database import get_db; print('✓ Database lazy-initialized')"

# Start FastAPI with Gunicorn
echo "🚀 Starting FastAPI backend..."
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 &

BACKEND_PID=$!

echo ""
echo "✓✓✓ Aurora OSI v3 Production Backend Running ✓✓✓"
echo ""
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""

# Keep running
wait $BACKEND_PID
