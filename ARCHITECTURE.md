# Architecture: GitHub Actions + Vercel + Railway

## Overview

Aurora OSI v3 is deployed using a modern full-stack architecture:

```
GitHub Repository
    ↓
GitHub Actions Workflow
    ├→ Frontend (npm build)
    │  └→ Vercel Deployment
    │     └→ Served on aurora-osi.vercel.app
    │
    └→ Backend (Python app)
       └→ Railway Deployment
          └→ REST API on Railway
             └→ PostgreSQL + Redis
```

## Components

### Frontend (Vercel)
- **Platform**: Vercel
- **Framework**: React 18 + TypeScript + Vite
- **URL**: https://aurora-osi.vercel.app
- **Build**: Automatic on push to main
- **CDN**: Vercel Global CDN (automatic)

### Backend (Railway)
- **Platform**: Railway
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **Region**: Global (user-configurable)
- **Auto-scaling**: Yes (Railway managed)
- **Memory**: Scalable per deployment
- **Database**: PostgreSQL (Railway managed)
- **Cache**: Redis (Railway managed)

### Database (Railway PostgreSQL)
- **Platform**: Railway Managed PostgreSQL
- **Engine**: PostgreSQL 15
- **Backups**: Automatic daily backups
- **Retention**: 30 days

### Cache (Railway Redis)
- **Platform**: Railway Managed Redis
- **Engine**: Redis 7.0
- **Region**: Auto-selected by Railway

## Deployment Flow

1. **Developer pushes to main branch**
   ```
   git push origin main
   ```

2. **GitHub Actions triggered**
   - Checks out code
   - Runs linting and tests
   - Builds frontend and backend

3. **Frontend deployment**
   - npm ci + npm run build
   - Deploy to Vercel
   - CDN cache invalidation

4. **Backend deployment**
   - Install Python dependencies
   - Deploy to Railway
   - Environment variables auto-injected
   - Health check verification

5. **Services online**
   - Frontend: https://aurora-osi.vercel.app
   - Backend: https://aurora-backend-xxx.railway.app
   - Database & Cache: Auto-provisioned

## Cost Optimization

| Service | Estimate | Notes |
|---------|----------|-------|
| Railway Backend | $0/month* | Free tier with usage limits |
| Railway PostgreSQL | $0/month* | Included in free tier |
| Railway Redis | $0/month* | Included in free tier |
| Vercel Frontend | Free | Included with free tier |
| **Total** | **$0/month*** | Completely free during development |

*Free tier includes generous limits; upgrade as traffic grows (~$5-20/month typical)

## Monitoring & Logs

### Cloud Run Logs
```bash
gcloud run services logs read aurora-backend --region us-central1 --limit=100
```

### Deployment Status
```bash
gcloud run services describe aurora-backend --region us-central1
```

### GitHub Actions
https://github.com/tulwegroup/aurora-githubpages/actions

### Vercel Dashboard
https://vercel.com/dashboard

## Security

- **No secrets in code** - All sensitive data in GitHub Secrets
- **Workload Identity Federation** - No service account keys needed
- **Container signing** - Images verified before deployment
- **Network isolation** - VPC connector for database access
- **HTTPS enforced** - All connections encrypted

## Scaling

### Horizontal Scaling
- Cloud Run automatically scales 1-100 instances
- Load balancer distributes traffic
- No additional configuration needed

### Vertical Scaling
- Increase memory: Modify Cloud Run deployment
- Increase CPU cores: Same deployment command
- Update in workflow file and redeploy

## Rollback

### Quick Rollback (Cloud Run)
```bash
# View all revisions
gcloud run services describe aurora-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic aurora-backend \
  --region us-central1 \
  --to-revisions PREVIOUS=100
```

### Frontend Rollback (Vercel)
- Use Vercel Dashboard → Settings → Deployments → Rollback

## Performance

- **Frontend**: Cached on Vercel CDN (~50ms globally)
- **Backend**: Responds in ~200-500ms (depends on database)
- **Database**: Connection pooling for optimal throughput
- **Redis**: In-memory cache for frequently accessed data

## Disaster Recovery

1. **Database Backup**
   - Automatic daily backups in GCP
   - Retention: 30 days

2. **Code Recovery**
   - Git history available on GitHub
   - All deployments tagged and versioned

3. **Recovery Time Objective (RTO)**
   - Frontend: < 5 minutes (redeploy to Vercel)
   - Backend: < 10 minutes (rebuild and deploy to Cloud Run)

## Migration from Railway

### Key Differences

| Aspect | Railway | Cloud Run |
|--------|---------|-----------|
| Pricing | Fixed ~$12/mo | Pay-per-use (~$5-20/mo) |
| Scaling | Manual | Automatic (1-100 instances) |
| Cold starts | Minimal | ~2-3 seconds (acceptable) |
| Database | Managed | Separate service (more control) |
| Deployment | Git-based | Docker-based (more control) |

### Benefits

1. **Cost**: Pay only for what you use
2. **Scale**: Automatic horizontal scaling
3. **Reliability**: SLA-backed service (99.95%)
4. **Control**: Full Docker customization
5. **Integration**: Native GCP ecosystem
