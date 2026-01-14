# Aurora OSI v3 - Deployment Guide

## Quick Start

### Prerequisites
- GitHub account with PAT token (for authentication)
- Google Cloud project with billing enabled
- Vercel account with project set up
- Docker installed locally
- `gcloud` CLI installed

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/tulwegroup/aurora-githubpages.git
cd aurora-githubpages

# Install dependencies
npm install
pip install -r backend/requirements.txt
```

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

**Frontend Secrets:**
- `VERCEL_TOKEN` - Vercel authentication token
- `ORG_ID` - Vercel organization ID
- `PROJECT_ID` - Vercel project ID

**Backend Secrets:**
- `GCP_PROJECT_ID` - Google Cloud project ID
- `WIF_PROVIDER` - Workload Identity Federation provider
- `WIF_SERVICE_ACCOUNT` - Service account email
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### 3. Deploy Locally for Testing

```bash
# Build frontend
npm run build

# Test backend locally
cd backend
python -m uvicorn main:app --reload

# In another terminal, test API
curl http://localhost:8000/system/health
```

### 4. Push to Trigger Automated Deployment

```bash
git add .
git commit -m "Deploy Aurora OSI v3"
git push origin main
```

GitHub Actions will automatically:
1. Build and deploy frontend to Vercel
2. Build and deploy backend to Google Cloud Run
3. Run database migrations

## Production Deployment Checklist

- [ ] Google Cloud project created and configured
- [ ] Service account with proper permissions
- [ ] Workload Identity Federation configured
- [ ] Cloud SQL PostgreSQL instance running
- [ ] Memorystore Redis instance running
- [ ] GitHub repository secrets configured
- [ ] Vercel project created
- [ ] Environment variables verified

## Monitoring

### View Backend Logs
```bash
gcloud run services logs read aurora-backend --region us-central1 --limit=50
```

### View Deployment Status
```bash
gcloud run services describe aurora-backend --region us-central1
```

### Check GitHub Actions
https://github.com/tulwegroup/aurora-githubpages/actions

## Rollback

### Cloud Run Rollback
```bash
# List all revisions
gcloud run services describe aurora-backend --region us-central1

# Traffic to previous revision
gcloud run services update-traffic aurora-backend \
  --region us-central1 \
  --to-revisions PREVIOUS=100
```

### Vercel Rollback
Use Vercel Dashboard → Settings → Deployments → Rollback

## Troubleshooting

### "Service account not found"
- Ensure `WIF_SERVICE_ACCOUNT` secret is set correctly
- Verify service account email format

### "Docker build failed"
- Check `backend.Dockerfile` exists
- Run locally: `docker build -t aurora-backend -f backend.Dockerfile .`

### "Database connection error"
- Verify `DATABASE_URL` in GitHub secrets
- Ensure Cloud SQL instance is running
- Check VPC connector configuration

### "Cold start delays"
- Normal for Cloud Run (~2-3 seconds on first request)
- Set `min-instances` to 1 to avoid cold starts
- Upgrade instance type if needed

## Cost Optimization Tips

1. **Cloud Run**: 
   - Set `min-instances: 0` for development
   - Set `min-instances: 1` for production
   - Monitor actual usage and adjust

2. **Cloud SQL**:
   - Use smaller instance for development
   - Enable automatic backups (included)
   - Monitor connection pool size

3. **Memorystore**:
   - Start with 1GB instance
   - Monitor eviction rate
   - Upgrade if necessary

4. **Cloud Build**:
   - GitHub Actions handles builds (cost-effective)
   - Free tier includes 120 mins/month

## Performance Tips

1. **Frontend**:
   - Images are automatically optimized by Vercel
   - Use code splitting for large bundles
   - Enable Vercel Analytics

2. **Backend**:
   - Database connection pooling enabled
   - Redis caching for frequent queries
   - Async task processing for long operations

3. **Database**:
   - Create indexes on frequently queried columns
   - Monitor slow query logs
   - Archive old data periodically

## Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets
2. **Rotate credentials regularly** - Update secrets every 90 days
3. **Use VPC connector** - Database only accessible from VPC
4. **Enable Cloud Armor** - DDoS protection for Cloud Run
5. **Monitor access logs** - Enable Cloud Logging

## Support

- Documentation: See [ARCHITECTURE.md](ARCHITECTURE.md)
- Issues: https://github.com/tulwegroup/aurora-githubpages/issues
- Email: support@aurora-osi.dev

## What's Next?

- [ ] Set up monitoring alerts
- [ ] Configure backup schedules
- [ ] Implement blue-green deployments
- [ ] Add load testing
- [ ] Set up API rate limiting
- [ ] Implement request signing
- [ ] Add request/response caching
