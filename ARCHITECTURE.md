# Architecture: GitHub Actions + Vercel + Google Cloud Run

## Overview

Aurora OSI v3 is deployed using a modern serverless architecture:

```
GitHub Repository
    ↓
GitHub Actions Workflow
    ├→ Frontend (npm build)
    │  └→ Vercel Deployment
    │     └→ Served on aurora-osi.vercel.app
    │
    └→ Backend (Docker build)
       ├→ Google Container Registry
       └→ Cloud Run Deployment
          └→ REST API on Cloud Run
```

## Components

### Frontend (Vercel)
- **Platform**: Vercel
- **Framework**: React 18 + TypeScript + Vite
- **URL**: https://aurora-osi.vercel.app
- **Build**: Automatic on push to main
- **CDN**: Vercel Global CDN (automatic)

### Backend (Google Cloud Run)
- **Platform**: Google Cloud Run
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **Container Registry**: Google Container Registry (gcr.io)
- **Region**: us-central1
- **Auto-scaling**: 1-100 instances
- **Memory**: 2GB per instance
- **CPU**: 2 vCPU per instance

### Database (Cloud SQL)
- **Platform**: Google Cloud SQL
- **Engine**: PostgreSQL 15
- **Instance**: aurora-db (db-f1-micro)
- **Region**: us-central1
- **Backup**: Automatic daily backups

### Cache (Memorystore)
- **Platform**: Google Cloud Memorystore
- **Engine**: Redis 7.0
- **Size**: 1GB
- **Region**: us-central1

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
   - Build Docker image
   - Push to Google Container Registry
   - Deploy new revision to Cloud Run
   - Update traffic routing (100% to new revision)

5. **Database migration** (if needed)
   - Run database schema updates
   - Seed data if necessary

## Cost Optimization

| Service | Estimate | Notes |
|---------|----------|-------|
| Cloud Run | ~$5-20/month | Auto-scales, charged per invocation |
| Cloud SQL | ~$10-15/month | db-f1-micro tier |
| Memorystore Redis | ~$10-15/month | 1GB instance |
| Cloud Build | ~$0.003/build-minute | Free tier: 120 mins/month |
| Container Registry | ~$0.10/GB | Minimal storage for one image |
| **Total** | **~$35-65/month** | Scales with traffic |

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
