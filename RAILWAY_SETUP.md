# Aurora OSI v3 - Railway Deployment Guide

## Overview

Aurora OSI v3 is deployed to Railway with:
- **Frontend**: Vercel (automatic)
- **Backend**: Railway (automatic via GitHub Actions)
- **Database**: Railway PostgreSQL
- **Cache**: Railway Redis
- **Secrets**: Railway environment variables (including GEE service key)

## Quick Setup (5 minutes)

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "GitHub Repo" → authorize → select `aurora-githubpages`
4. Railway will auto-detect and create services

### Step 2: Add Required Services

In Railway dashboard:

```
Aurora OSI Project
├── aurora-backend (GitHub linked)
├── PostgreSQL (click + Add)
└── Redis (click + Add)
```

**Add PostgreSQL:**
- Click "+" in Railway dashboard
- Select "Database" → "PostgreSQL"
- Railway auto-links to backend as DATABASE_URL

**Add Redis:**
- Click "+" in Railway dashboard
- Select "Database" → "Redis"
- Railway auto-links to backend as REDIS_URL

### Step 3: Configure GEE Service Key

**Get your GEE service account JSON key:**
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create service account or use existing
3. Create JSON key
4. Copy the entire JSON content

**Add to Railway:**
1. In Railway dashboard → Variables
2. Add new variable: `GEE_SERVICE_ACCOUNT_FILE`
3. Paste the entire JSON key content (as-is)

Or use Railway CLI:
```bash
railway variables set GEE_SERVICE_ACCOUNT_FILE='{"type": "service_account", ...}'
```

### Step 4: Add GitHub Secrets

In your GitHub repository (Settings → Secrets → Actions):

```
RAILWAY_TOKEN          = Your Railway API token (from railway.app/account/tokens)
RAILWAY_PROJECT_ID     = Your Railway project ID (from railway.app/project)
VERCEL_TOKEN           = Your Vercel token
ORG_ID                 = Your Vercel org ID
PROJECT_ID             = Your Vercel project ID
```

To get Railway token:
```bash
# Or from UI: https://railway.app/account/tokens
railway login
```

### Step 5: Deploy!

```bash
git push origin main
```

GitHub Actions will:
1. Build and deploy frontend to Vercel
2. Build and deploy backend to Railway
3. Database + Redis auto-configured

Done! ✅

---

## Railway Features

### Auto-Database Linking

Railway automatically injects connection strings:
- `DATABASE_URL` → PostgreSQL connection
- `REDIS_URL` → Redis connection

### Health Checks

Railway monitors `/system/health` endpoint for deployment status.

### Automatic Deployments

Every push to `main` branch triggers:
1. Docker image build (if Dockerfile exists)
2. Service deployment
3. Health check verification

### Logs

View logs in Railway dashboard or CLI:
```bash
railway logs -f
```

### Environment Variables

Set in Railway dashboard:
- Variables are injected at runtime
- Secrets are encrypted
- Change takes effect on next deploy

---

## GEE Service Account Key Setup

### Option 1: Add via Railway UI

1. Go to your project → Variables
2. Click "Raw Editor"
3. Add:
   ```
   GEE_SERVICE_ACCOUNT_FILE={"type":"service_account","project_id":"..."}
   ```

### Option 2: Add via Railway CLI

```bash
railway link <project-id>
railway variables set GEE_SERVICE_ACCOUNT_FILE='<json-content>'
```

### Option 3: Add via GitHub Secrets

1. Store GEE JSON in GitHub secret: `GEE_SERVICE_KEY_JSON`
2. In Railway variables, reference it:
   ```
   GEE_SERVICE_ACCOUNT_FILE=${{ secrets.GEE_SERVICE_KEY_JSON }}
   ```

### Verify GEE Setup

Test the Earth Engine integration:
```bash
curl https://your-railway-backend-url.railway.app/system/health
```

---

## Troubleshooting

### Service won't start

**Check logs:**
```bash
railway logs -f
```

**Common issues:**
- Python dependencies missing → `pip install -r backend/requirements.txt`
- PORT env var not set → Railway auto-sets to 3000
- Import errors → Check `backend/main.py` imports

### Database connection failed

1. Verify PostgreSQL service is running (green icon in Railway)
2. Check `DATABASE_URL` in Railway variables
3. Restart backend service

### GEE integration not working

1. Verify `GEE_SERVICE_ACCOUNT_FILE` is set in Railway variables
2. Test with: `curl .../system/config` to see loaded settings
3. Check backend logs for authentication errors

### Frontend not connecting to backend

1. Verify backend service URL is correct
2. Check CORS settings in `backend/config.py`
3. Frontend should use Railway URL: `https://aurora-backend-xxx.railway.app`

---

## Managing Services

### Scale Backend

Railway automatically scales based on traffic. To control:

1. **Reduce costs**: Reduce allocated memory/CPU
2. **Increase performance**: Increase memory/CPU
3. In Railway dashboard → Settings → Resources

### Backup Database

PostgreSQL on Railway:
- Automatic daily backups
- Retention: 30 days
- Restore via Railway UI

### Monitor Usage

Railway dashboard shows:
- CPU/Memory usage
- Network I/O
- Deployment history
- Cost tracking

---

## Production Checklist

- [ ] PostgreSQL service running
- [ ] Redis service running
- [ ] GEE_SERVICE_ACCOUNT_FILE set in variables
- [ ] GitHub secrets configured (5 secrets)
- [ ] Database initialized (migrations ran)
- [ ] Health endpoint responding
- [ ] Frontend connects to backend
- [ ] API endpoints working

---

## Deployment Flow

```
git push origin main
         ↓
GitHub Actions Workflow Triggered
         ↓
    ┌────┴────┐
    ↓         ↓
Frontend    Backend
(Vercel)   (Railway)
    ↓         ↓
Build      Test
    ↓         ↓
Deploy    Build Docker
    ↓         ↓
Live      Deploy to Railway
    ↓         ↓
cdn        Health Check
    ↓         ↓
    └────┬────┘
         ↓
    ✅ Live
```

---

## Cost

**Aurora OSI on Railway (free tier):**
- Backend: **$0** (includes free tier)
- PostgreSQL: **$0** (included)
- Redis: **$0** (included)
- **Total: $0/month** (free tier)

**When you exceed free tier:**
- Usage-based pricing (~$5-20/month typically)
- Only pay for what you use
- No minimum charges

---

## Next: Monitoring & Scaling

Once deployed:

1. **Monitor**: Check Railway dashboard regularly
2. **Logs**: `railway logs -f`
3. **Scale**: Increase resources if needed
4. **Optimize**: Monitor database queries

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway CLI**: `railway help`
- **GitHub Actions**: `gh workflow view deploy.yml`
- **Backend Logs**: Railway dashboard → Logs tab

Happy deploying! 🚀
