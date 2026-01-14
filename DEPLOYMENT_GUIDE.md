# Aurora OSI v3 - Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                          │
│                      React + TypeScript                         │
│                    aurora-osi-v3-frontend                       │
│                                                                 │
│  Dashboard | Mineral Detection | Digital Twin | Seismic View   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                        HTTPS/REST
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
┌───────▼────────────────────────┐    ┌──────────▼─────────┐
│   Backend API (Railway)        │    │  Cache (Redis)     │
│   FastAPI + Gunicorn           │    │  Railway Redis     │
│   aurora-osi-v3-api            │    │  (Standalone)      │
│                                │    └────────────────────┘
│ - Mineral Detection            │
│ - Digital Twin Queries         │
│ - Satellite Tasking            │
│ - Seismic Processing           │
│ - Physics Constraints          │
│ - Quantum Inversion            │
└───────┬────────────────────────┘
        │
        │ PostgreSQL (TCP 5432)
        │
    ┌───▼──────────────────────┐
    │  Database (Neon)         │
    │  PostgreSQL 15           │
    │                          │
    │ Tables:                  │
    │ - mineral_detections     │
    │ - digital_twin_voxels    │
    │ - satellite_tasks        │
    │ - seismic_twin           │
    │ - physics_residuals      │
    └────────────────────────────┘
```

## Prerequisites

1. **Vercel Account:** https://vercel.com
2. **Railway Account:** https://railway.app
3. **Neon Account:** https://neon.tech
4. **GitHub Repository:** Your code must be in GitHub
5. **Environment Variables:** See `.env.example`

## Part 1: Neon PostgreSQL Setup

### 1.1 Create Neon Project

1. Go to https://neon.tech and sign in
2. Click **Create a new project**
3. Enter project name: `aurora-osi-v3`
4. Select region closest to your deployment (e.g., `us-east-1`)
5. Click **Create project**

### 1.2 Configure Database

1. In Neon dashboard, click your project
2. Note the **Connection String**:
   ```
   postgresql://user:password@endpoint.neon.tech/aurora_osi_v3
   ```
3. Save the connection string for later

### 1.3 Initialize Schema

Run migrations on Neon (backend will auto-create tables):
```bash
export DATABASE_URL="postgresql://user:password@endpoint.neon.tech/aurora_osi_v3"
python -c "from backend.database import DatabaseManager; db = DatabaseManager()"
```

## Part 2: Railway Backend Deployment

### 2.1 Create Railway Project

1. Go to https://railway.app and sign in
2. Click **New Project**
3. Select **Deploy from GitHub**
4. Choose your `aurora-osi-v3` repository
5. Click **Deploy**

### 2.2 Configure Environment Variables

In Railway dashboard:

1. Click your project
2. Click the **Backend** service
3. Click **Variables**
4. Add the following environment variables:

```
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/aurora_osi_v3
REDIS_URL=redis://:password@redis-service:6379/0
SECRET_KEY=your-secret-key-here-min-32-chars
API_PORT=8000
WORKERS=4
GUNICORN_TIMEOUT=120
LOG_LEVEL=INFO
```

⚠️ **Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.3 Configure Build & Deploy Settings

1. Click your project name
2. Go to **Settings** > **Deploy**
3. Set:
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `bash backend/start.sh`
   - **Root Directory:** `/`
   - **Watch Paths:** `backend/**`

### 2.4 Add Redis Service (Optional but Recommended)

1. Click **+ Add Service**
2. Select **Redis**
3. Railway will auto-generate `REDIS_URL`
4. Update your backend `REDIS_URL` variable if needed

### 2.5 Connect Neon Database

1. Click **+ Add Service**
2. Select **Neon**
3. Authenticate with Neon account
4. Select your `aurora-osi-v3` project
5. Click **Connect**

Railway will auto-populate `DATABASE_URL`.

### 2.6 Deploy

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Ready for production deployment"
   git push origin main
   ```

2. Railway will automatically build and deploy
3. View logs: **Logs** tab in Railway dashboard
4. Get API URL: Click **Settings** > **Public Networking**

**Example URL:** `https://aurora-osi-v3-api-prod.railway.app`

## Part 3: Vercel Frontend Deployment

### 3.1 Create Vercel Project

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Select **Project Type:** React
4. Click **Import**

### 3.2 Configure Environment Variables

In Vercel:

1. Click **Settings** > **Environment Variables**
2. Add:

```
VITE_API_URL=https://your-railway-backend-url
VITE_ENV=production
VITE_LOG_LEVEL=info
```

Replace `your-railway-backend-url` with actual Railway API URL from Part 2.

### 3.3 Configure Build Settings

1. **Build Command:**
   ```
   npm run build
   ```

2. **Output Directory:**
   ```
   dist
   ```

3. **Install Command:**
   ```
   npm install
   ```

### 3.4 Deploy

Vercel automatically deploys on push to main branch:

```bash
git push origin main
```

View deployment at: https://aurora-osi-v3.vercel.app

## Part 4: GitHub Actions CI/CD

### 4.1 Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install backend dependencies
        run: pip install -r backend/requirements.txt pytest
      
      - name: Install frontend dependencies
        run: npm install
      
      - name: Run backend tests
        run: pytest backend/ -v
      
      - name: Build frontend
        run: npm run build
        env:
          VITE_API_URL: https://aurora-osi-v3-api-prod.railway.app
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: success()
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy via Railway
        run: |
          npm install -g @railway/cli
          railway link --projectId ${{ secrets.RAILWAY_PROJECT_ID }}
          railway deploy --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### 4.2 Add GitHub Secrets

1. Go to GitHub repository
2. **Settings** > **Secrets and variables** > **Actions**
3. Add:
   - `RAILWAY_TOKEN`: Your Railway API token
   - `RAILWAY_PROJECT_ID`: Your Railway project ID

## Part 5: Monitoring & Logging

### 5.1 Railway Logs

View in Railway dashboard:
- Click project
- Click **Logs** tab
- Filter by service (Backend, Database)

### 5.2 Health Checks

Railway uses `/health` endpoint for health checks (configured in `railway.toml`).

Test manually:
```bash
curl https://your-railway-backend-url/health
```

### 5.3 Database Monitoring

Neon provides:
- Query performance insights
- Storage monitoring
- Connection pool status

Access at: https://console.neon.tech

### 5.4 Frontend Monitoring

Vercel provides:
- Deploy logs
- Runtime errors
- Performance metrics

Access at: https://vercel.com/dashboard

## Part 6: Domain Configuration

### 6.1 Connect Custom Domain (Vercel)

1. In Vercel: **Settings** > **Domains**
2. Add your domain (e.g., `aurora-osi-v3.com`)
3. Follow DNS configuration instructions
4. Update MX records if using email

### 6.2 Connect Custom Domain (Railway)

1. In Railway: Click your backend service
2. **Settings** > **Public Networking**
3. Add custom domain
4. Configure DNS records

## Part 7: Security Hardening

### 7.1 Environment Variables

Never commit `.env` files:
```bash
echo ".env" >> .gitignore
```

### 7.2 Database Backups

Neon automatically backs up daily. To restore:
1. Go to Neon console
2. **Backups** tab
3. Select backup date
4. Click **Restore**

### 7.3 API Security

- Enable HTTPS only (both platforms do this by default)
- Rotate API keys regularly
- Use environment-specific secrets
- Implement rate limiting (add to FastAPI)

### 7.4 Database Security

- Use strong passwords (Neon generates these)
- Enable IP whitelisting if available
- Use SSL connections only
- Regular security audits

## Troubleshooting

### Backend Deploy Fails

**Check logs:**
```bash
railway logs --service backend
```

**Common issues:**
- Missing environment variables
- Database connection timeout
- Port conflicts (must use 8000)

**Solution:**
```bash
# Verify variables
railway variables
# Restart service
railway redeploy --service backend
```

### Frontend Can't Connect to Backend

**Check CORS:**
```bash
curl -H "Origin: https://aurora-osi-v3.vercel.app" \
  https://your-railway-backend-url/health
```

**Fix:** Ensure backend has correct CORS headers in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aurora-osi-v3.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Connection Timeout

**Increase timeout in Railway settings:**
- Backend: Add `GUNICORN_TIMEOUT=300` to variables
- Connection pool: Adjust `pool_size` in `database.py`

### Build Fails

**Check Node/Python versions:**
```bash
node --version  # Should be 18+
python --version  # Should be 3.11+
```

**Clear cache and rebuild:**
- Vercel: **Settings** > **Git** > **Clear Build Cache**
- Railway: **Redeploy** with fresh build

## Production Checklist

- [ ] All environment variables configured
- [ ] Database initialized with schema
- [ ] SSL certificates enabled
- [ ] Health checks passing
- [ ] Logs accessible and monitored
- [ ] Backups configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Error tracking integrated
- [ ] Performance monitoring active
- [ ] Custom domain configured
- [ ] DNS records updated
- [ ] Load testing completed
- [ ] Security audit passed

## Scaling & Performance

### Database Scaling (Neon)

1. Monitor connection count
2. Upgrade plan if needed
3. Increase compute size for large queries

### Backend Scaling (Railway)

1. Monitor CPU/memory usage
2. Increase worker count in `start.sh`
3. Scale horizontally with multiple replicas

### Frontend Caching (Vercel)

1. Add long-lived cache headers
2. Enable edge caching
3. Use CDN for static assets

## Disaster Recovery

### Database Restore

```bash
# From Neon backup
psql postgresql://user:pass@endpoint.neon.tech/aurora_osi_v3 < backup.sql
```

### Rollback Deployment

**Vercel:**
- Click deployment in history
- Click **Promote to Production**

**Railway:**
- Click deployment history
- Select previous deployment
- Click **Rollback**

---

**Last Updated:** January 14, 2026  
**Environment:** Production
