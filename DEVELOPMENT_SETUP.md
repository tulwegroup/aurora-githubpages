# Aurora OSI v3 - Development Setup Guide

## System Requirements

- **OS:** Windows 10+, macOS 10.15+, or Ubuntu 20.04+
- **CPU:** 4+ cores recommended
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 10GB free space

## Prerequisites

Install these tools first:

### 1. Git
- **Windows:** https://git-scm.com/download/win
- **macOS:** `brew install git`
- **Linux:** `sudo apt-get install git`

Verify:
```bash
git --version
```

### 2. Python 3.11+
- **Windows:** https://www.python.org/downloads/
- **macOS:** `brew install python@3.11`
- **Linux:** `sudo apt-get install python3.11 python3.11-venv python3.11-dev`

Verify:
```bash
python --version  # Should be 3.11+
```

### 3. Node.js 18+
- **Windows/macOS:** https://nodejs.org/ (Download LTS)
- **Linux:** `sudo apt-get install nodejs npm`

Verify:
```bash
node --version  # Should be 18+
npm --version   # Should be 9+
```

### 4. Docker
- **Windows/macOS:** https://www.docker.com/products/docker-desktop
- **Linux:** `sudo apt-get install docker.io docker-compose`

Verify:
```bash
docker --version
docker-compose --version
```

### 5. Git LFS (Large File Storage)
- Download: https://git-lfs.com
- Or: `brew install git-lfs` (macOS)

Verify:
```bash
git lfs --version
```

---

## Repository Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/aurora-osi-v3.git
cd aurora-osi-v3
```

### 2. Create Environment Files

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your local settings:
```bash
# .env (Development)
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aurora_osi_v3
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-not-for-production
API_PORT=8000
LOG_LEVEL=DEBUG
```

### 3. Copy to Backend

```bash
cp .env backend/.env
```

---

## Backend Setup

### 1. Create Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Start Database Services

Option A: Using Docker Compose (Recommended)
```bash
docker-compose up -d postgres redis
```

Option B: Manual installation
- **PostgreSQL:** https://www.postgresql.org/download/
- **Redis:** https://redis.io/download

### 5. Initialize Database

The backend will auto-create tables on first run. To manually initialize:

```bash
python -c "from backend.database import DatabaseManager; db = DatabaseManager()"
```

Verify database:
```bash
# Connect to PostgreSQL
psql -U postgres -d aurora_osi_v3

# In psql shell:
\dt  # List tables
SELECT version();  # Check server version
\q   # Quit
```

### 6. Start Backend Server

**Development (Auto-reload):**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production (with Gunicorn):**
```bash
cd backend
bash start.sh
```

Check health:
```bash
curl http://localhost:8000/health
```

View API docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Frontend Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Connection

Edit `.env`:
```bash
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

### 3. Start Development Server

```bash
npm run dev
```

Access at: http://localhost:5173

### 4. Build for Production

```bash
npm run build
# Output in: dist/
```

Preview build:
```bash
npm run preview
```

---

## Docker Development

### Option 1: Full Stack with Docker Compose (Easiest)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI Backend (port 8000)
- Nginx Proxy (port 80)

View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
```

Stop:
```bash
docker-compose down
```

### Option 2: Quick Start Script

```bash
bash quick_start.sh
```

This handles all setup and starts the development environment.

---

## Project Structure

```
aurora-osi-v3/
├── backend/                    # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── database.py            # PostgreSQL connection & schema
│   ├── models.py              # Pydantic data models
│   ├── config.py              # Configuration management
│   ├── database/
│   │   └── spectral_library.py  # Mineral spectral data
│   ├── routers/               # API route modules
│   │   └── system.py
│   ├── workers/               # Background tasks
│   │   └── mineral_worker.py
│   ├── integrations/          # External service integrations
│   │   └── gee_fetcher.py
│   ├── processing/            # Data processing modules
│   │   └── mineral_detector.py
│   ├── requirements.txt        # Python dependencies
│   ├── start.sh               # Production startup script
│   └── test_main.py           # Test suite
│
├── src/                       # React/TypeScript source
│   ├── App.tsx                # Main app component
│   ├── index.tsx              # Entry point
│   ├── api.ts                 # API client
│   ├── components/            # React components
│   │   ├── Dashboard.tsx
│   │   ├── SeismicView.tsx
│   │   ├── MapVisualization.tsx
│   │   └── ...
│   ├── config.ts              # Frontend config
│   └── constants.ts           # Constants
│
├── components/                # Shared components (legacy)
├── db/                        # Database migrations
│   └── migrations/
│       └── 0001_initial_schema.sql
│
├── package.json               # npm dependencies
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite bundler config
├── docker-compose.yml         # Development stack
├── backend.Dockerfile         # Backend containerization
├── frontend.Dockerfile        # Frontend containerization
│
├── .env.example               # Environment template
├── .env                       # Local config (not committed)
│
├── README.md                  # Project overview
├── API_DOCUMENTATION.md       # API reference
├── DEPLOYMENT_GUIDE.md        # Production deployment
├── TESTING_GUIDE.md           # Testing instructions
└── DEVELOPMENT_SETUP.md       # This file
```

---

## Common Commands

### Backend

```bash
# Start development server
cd backend && uvicorn main:app --reload

# Run tests
pytest -v

# Format code
black .
autopep8 --in-place --aggressive --aggressive *.py

# Check types
mypy .

# Run specific test
pytest backend/test_main.py::TestHealthEndpoints -v

# Generate coverage report
pytest --cov=backend --cov-report=html
```

### Frontend

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check

# Lint code
npm run lint

# Format code
npm run format

# Run tests (when configured)
npm test
```

### Docker

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec backend bash
```

### Database

```bash
# Connect to PostgreSQL
psql -U postgres -d aurora_osi_v3

# Common psql commands:
\dt              # List tables
\d table_name    # Describe table
SELECT * FROM mineral_detections LIMIT 5;  # Query data
\q               # Quit

# Backup database
pg_dump -U postgres aurora_osi_v3 > backup.sql

# Restore database
psql -U postgres aurora_osi_v3 < backup.sql

# Drop and recreate (⚠️ WARNING: Deletes all data)
dropdb -U postgres aurora_osi_v3
createdb -U postgres aurora_osi_v3
```

---

## IDE Setup

### VS Code (Recommended)

**Extensions to install:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Prettier - Code formatter (esbenp.prettier-vscode)
- Docker (ms-vscode.docker)
- REST Client (humao.rest-client)

**Settings (.vscode/settings.json):**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "editor.rulers": [80, 120]
}
```

### PyCharm

1. Open project
2. **Preferences** > **Project** > **Python Interpreter**
3. Select virtual environment from `./venv`
4. Configure run configuration for `uvicorn main:app --reload`

### WebStorm

1. Open project
2. **Settings** > **Languages & Frameworks** > **Node.js**
3. Select Node interpreter
4. Configure npm run dev

---

## Debugging

### Python Debugging

**VS Code Debug Config (.vscode/launch.json):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "jinja": true
    }
  ]
}
```

**Debug with print:**
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### JavaScript Debugging

**Browser DevTools:**
- Press F12 in browser
- Go to **Console** tab to see errors
- Use **Network** tab to inspect API calls
- Use **Sources** tab for breakpoints

**VS Code Debug:**
```json
{
  "name": "Vite",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:5173",
  "webRoot": "${workspaceFolder}"
}
```

### API Testing

**Using REST Client extension:**

Create `requests.http`:
```http
### Health Check
GET http://localhost:8000/health

### Detect Mineral
POST http://localhost:8000/detect/mineral
Content-Type: application/json

{
  "latitude": -20.5,
  "longitude": 134.5,
  "mineral": "arsenopyrite",
  "sensor": "Sentinel-2"
}
```

Right-click any request and select "Send Request"

---

## Troubleshooting

### Backend Won't Start

**Check Python version:**
```bash
python --version
```

**Check dependencies:**
```bash
pip list | grep fastapi
```

**Check port availability:**
```bash
# Windows (PowerShell)
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000
```

**Kill process on port 8000:**
```bash
# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# macOS/Linux
lsof -ti :8000 | xargs kill -9
```

### Database Connection Failed

**Check PostgreSQL is running:**
```bash
# Docker
docker-compose ps postgres

# Manual
psql -U postgres
```

**Test connection:**
```bash
psql -U postgres -h localhost -d aurora_osi_v3
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d postgres
```

### Frontend Won't Start

**Clear node_modules:**
```bash
rm -rf node_modules
npm install
npm run dev
```

**Clear Vite cache:**
```bash
rm -rf node_modules/.vite
npm run dev
```

### Port Already in Use

**Change port in code:**
- Backend: `uvicorn main:app --port 8001`
- Frontend: `npm run dev -- --port 5174`

### Environment Variables Not Working

**Verify .env file:**
```bash
cat .env

# Should show all variables
```

**Reload shell:**
```bash
# Deactivate and reactivate virtual environment
deactivate
source venv/bin/activate
```

---

## Git Workflow

### Create Feature Branch
```bash
git checkout -b feature/mineral-detection-ui
```

### Make Changes
```bash
# Edit files
git status
git add .
git commit -m "Add mineral detection UI component"
```

### Push to GitHub
```bash
git push origin feature/mineral-detection-ui
```

### Create Pull Request
1. Go to GitHub repository
2. Click **Compare & pull request**
3. Add description
4. Click **Create pull request**

### Merge (After Review)
```bash
git checkout main
git pull origin main
git merge feature/mineral-detection-ui
git push origin main
```

---

## Performance Tips

### Backend Optimization

1. **Use connection pooling:**
   ```python
   from sqlalchemy.pool import NullPool
   engine = create_engine(DATABASE_URL, poolclass=NullPool)
   ```

2. **Add caching:**
   ```python
   from functools import lru_cache
   @lru_cache(maxsize=128)
   def get_mineral_data(mineral: str):
       ...
   ```

3. **Profile code:**
   ```bash
   pip install py-spy
   py-spy record -o profile.svg -- python -c "..."
   ```

### Frontend Optimization

1. **Code splitting:**
   ```typescript
   const Dashboard = lazy(() => import('./Dashboard'))
   ```

2. **Lazy loading images:**
   ```html
   <img loading="lazy" src="..." />
   ```

3. **Bundle analysis:**
   ```bash
   npm install vite-plugin-visualizer
   ```

---

## Next Steps

1. ✅ Complete the setup following this guide
2. Run `bash quick_start.sh` to verify everything works
3. Make a small code change to test the workflow
4. Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) to understand endpoints
5. Read [TESTING_GUIDE.md](TESTING_GUIDE.md) to write tests
6. Deploy to production using [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Last Updated:** January 14, 2026  
**Status:** Production Ready
