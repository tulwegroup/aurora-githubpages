#!/bin/bash
# Aurora OSI v3 - Quick Start Script
# Deploy locally with PostgreSQL and Redis

set -e

echo "🚀 Aurora OSI v3 - Quick Start"
echo "=============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ Node.js required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }

echo -e "${GREEN}✓ Dependencies OK${NC}"

# Setup backend
echo -e "${BLUE}Setting up backend...${NC}"
cd backend
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Start PostgreSQL container
echo -e "${BLUE}Starting PostgreSQL...${NC}"
docker run -d \
  --name aurora-postgres \
  -e POSTGRES_PASSWORD=aurora_password \
  -e POSTGRES_DB=aurora_osi \
  -p 5432:5432 \
  postgres:15 2>/dev/null || true

sleep 3

# Export database URL
export DATABASE_URL="postgresql://postgres:aurora_password@localhost:5432/aurora_osi"

# Start Redis container
echo -e "${BLUE}Starting Redis...${NC}"
docker run -d \
  --name aurora-redis \
  -p 6379:6379 \
  redis:7 2>/dev/null || true

sleep 2

# Start backend
echo -e "${BLUE}Starting FastAPI backend...${NC}"
python3 main.py &
BACKEND_PID=$!
sleep 3

# Setup frontend
echo -e "${BLUE}Setting up frontend...${NC}"
cd ../
npm install -q
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Start frontend
echo -e "${BLUE}Starting Vite frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✓✓✓ Aurora OSI v3 Running ✓✓✓${NC}"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
