# Aurora OSI v3 - Two-Service Railway Architecture

## Why Two Services?

The previous single-container approach caused:
- ❌ IPv4/IPv6 routing complexity (localhost resolves to IPv6 in Alpine)
- ❌ Proxy middleman issues (Express proxying to FastAPI)
- ❌ Service startup sequencing problems
- ❌ Mixed concerns (frontend and backend in one container)

**New architecture:**
- ✅ **Backend Service**: Pure FastAPI on its own Railway service with external URL
- ✅ **Frontend Service**: Pure React + Express on its own Railway service
- ✅ **Direct Communication**: Frontend calls backend via environment variable (no proxy)
- ✅ **Independent Scaling**: Each service scales independently

---

## Architecture

```
┌─────────────────────────────────────┐
│  Railway Project: aurora-osi-v3     │
└─────────────────────────────────────┘
        │                    │
        ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  Backend Service │  │ Frontend Service │
│  (FastAPI)       │  │ (React + Express)│
│  Port: 8000      │  │ Port: 3000       │
│  URL: aurora-    │  │ URL: aurora-     │
│  backend-prod... │  │ frontend-prod... │
└──────────────────┘  └──────────────────┘
        │
        │ $BACKEND_URL env var
        │
        ▼
   GEE Integration
   + Database
   + Spectral Library
```

---

## Step 1: Create Backend Service

### In Railway Dashboard:

1. **Create new service** → "Deploy from GitHub"
2. **Select Repository**: `aurora-githubpages`
3. **Configure**:
   - **Name**: `aurora-backend-prod`
   - **Dockerfile**: `backend.Dockerfile.production`
   - **Port**: `8000`

4. **Set Environment Variables**:
   ```
   DATABASE_URL=postgresql://[your-db-url]
   GEE_PROJECT_ID=aurora-osi-gee
   ENVIRONMENT=production
   DEBUG=false
   
   # CRITICAL: GEE Service Account
   # Option A: If you have service account JSON file
   GEE_SERVICE_ACCOUNT_JSON={"type": "service_account", "project_id": "...", ...}
   
   # Option B: If you have service account file path
   # GEE_SERVICE_ACCOUNT_FILE=/app/gee-credentials.json
   
   # Option C: Application Default Credentials (if using Railway's built-in GCP integration)
   # Leave GEE_* blank and it will attempt default initialization
   ```

5. **Deploy** → Wait for success

6. **Get Backend URL**: 
   - From Railway dashboard: `https://aurora-backend-prod.up.railway.app`
   - Copy this URL

---

## Step 2: Create Frontend Service

### In Railway Dashboard:

1. **Create new service** → "Deploy from GitHub"
2. **Select Repository**: `aurora-githubpages`
3. **Configure**:
   - **Name**: `aurora-frontend-prod`
   - **Dockerfile**: `frontend.Dockerfile.production`
   - **Port**: `3000`

4. **Set Environment Variables**:
   ```
   BACKEND_URL=https://[backend-service-url]:8000
   PORT=3000
   NODE_ENV=production
   ```
   
   Example:
   ```
   BACKEND_URL=https://aurora-backend-prod-production.up.railway.app:8000
   ```

5. **Deploy** → Wait for success

6. **Get Frontend URL**: 
   - From Railway dashboard: `https://aurora-frontend-prod.up.railway.app`
   - This is your live site

---

## Step 3: Verify Connectivity

### Frontend to Backend:

1. Open Frontend URL in browser
2. Open Developer Console (F12)
3. Check for any errors calling `/api/system/health`
4. Should see: `Backend: OPERATIONAL`

### Backend Health Check:

```bash
curl https://aurora-backend-prod-production.up.railway.app/health
# Response:
# {
#   "status": "operational",
#   "version": "3.1.0",
#   "database": "CONNECTED",
#   "gee": "INITIALIZED",
#   "timestamp": 1705591234.5
# }
```

---

## GEE Service Account Setup

### Option 1: Using Service Account JSON (Recommended)

1. **In Google Cloud Console**:
   - Create/download Service Account JSON key
   - Copy entire JSON content

2. **In Railway**:
   - Backend Service Settings → Variables
   - Add: `GEE_SERVICE_ACCOUNT_JSON`
   - Paste entire JSON as value
   - Redeploy

3. **Verification**:
   - Backend logs should show: `✅ GEE initialized with service account JSON`

### Option 2: Using Service Account File

1. **In Railway**:
   - Backend Service Settings → File System
   - Mount volume at `/app/gee-credentials.json`
   - Upload service account JSON
   - Set env var: `GEE_SERVICE_ACCOUNT_FILE=/app/gee-credentials.json`
   - Redeploy

### Option 3: Application Default Credentials

If Railway has GCP integration enabled:
- Leave `GEE_SERVICE_ACCOUNT_*` vars unset
- Railway will use its default GCP credentials

---

## Troubleshooting

### Frontend can't reach Backend

```bash
# Check BACKEND_URL is set correctly
curl https://[frontend-url]/api/system/health

# Should forward to backend. If 503:
# 1. Check BACKEND_URL env var in frontend service
# 2. Check backend service is running
# 3. Check backend URL is accessible (no auth/firewall issues)
```

### GEE not initializing

1. Check backend logs:
   ```
   Railway Dashboard → Backend Service → Logs
   Look for: "GEE initialized" or "GEE initialization failed"
   ```

2. Verify credentials:
   ```
   If using JSON:
   - Validate JSON is valid (not truncated)
   - Check "type": "service_account" is present
   
   If using file:
   - Verify file path is correct
   - Check file permissions
   ```

3. Check GEE_PROJECT_ID matches service account project

### Database connection issues

1. Verify DATABASE_URL in backend service
2. Check database is accessible from Railway
3. Look for PgBouncer connection limits (if using Railway PostgreSQL)

---

## Environment Variables Reference

### Backend Service

```
# Core
ENVIRONMENT=production
DEBUG=false
PORT=8000

# Database
DATABASE_URL=postgresql://[user:pass@host:port/db]
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# GEE (choose one method)
GEE_PROJECT_ID=aurora-osi-gee
GEE_SERVICE_ACCOUNT_JSON={...}     # Method 1: JSON string
# OR
GEE_SERVICE_ACCOUNT_FILE=/path/to/file  # Method 2: File path

# Security
SECRET_KEY=[generate-strong-key]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=https://[frontend-url]
```

### Frontend Service

```
# Core
NODE_ENV=production
PORT=3000

# Backend Connection
BACKEND_URL=https://[backend-service-url]:8000
```

---

## Monitoring

### In Railway Dashboard:

1. **Backend Service**:
   - Logs tab: Watch for startup errors
   - Metrics: CPU/Memory usage
   - Deployments: Version history

2. **Frontend Service**:
   - Logs tab: Proxy errors show here
   - Metrics: Request counts
   - Deployments: Version history

### Health Endpoint

Frontend continuously monitors backend at `GET /system/health`:
- Response includes: database status, GEE status, system version
- Shown in ConfigView component
- If unreachable, shows `Backend: OFFLINE`

---

## Rollback

If deployment fails:

1. **Backend Service**:
   - Railway Dashboard → Deployments → Previous version → Revert
   
2. **Frontend Service**:
   - Railway Dashboard → Deployments → Previous version → Revert
   - Check that BACKEND_URL is still correct

---

## Next Steps

1. Create backend service with `backend.Dockerfile.production`
2. Set backend environment variables (especially GEE credentials)
3. Wait for backend to be healthy
4. Create frontend service with `frontend.Dockerfile.production`
5. Set BACKEND_URL to the backend service URL
6. Verify both services are running and communicating
7. Monitor logs for any issues
