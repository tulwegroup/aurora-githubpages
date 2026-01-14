# Aurora OSI v3 - Railway Deployment Guide

## Deployment Stack

- **Frontend**: Vercel (auto-deployed)
- **Backend**: Railway (auto-deployed)
- **Database**: Railway PostgreSQL
- **Cache**: Railway Redis
- **CI/CD**: GitHub Actions

## Quick Start (5 minutes)

### 1. Create Railway Project

Go to https://railway.app:
1. Click "New Project"
2. Select "GitHub Repo" → select `aurora-githubpages`
3. Railway auto-detects and creates backend service

### 2. Add Services

Click "+" to add:
- **PostgreSQL** (auto-links as DATABASE_URL)
- **Redis** (auto-links as REDIS_URL)

### 3. Configure GEE

In Railway dashboard → Variables:
- Add `GEE_SERVICE_ACCOUNT_FILE` = your entire GEE service account JSON

### 4. Add GitHub Secrets

```bash
gh secret set RAILWAY_TOKEN --body "$(railway tokens create)"
gh secret set RAILWAY_PROJECT_ID --body "your-project-id"
gh secret set VERCEL_TOKEN --body "your-vercel-token"
gh secret set ORG_ID --body "your-org-id"
gh secret set PROJECT_ID --body "your-project-id"
```

### 5. Deploy!

```bash
git push origin main
```

✅ Done! Frontend and backend automatically deploy.

## Required GitHub Secrets

```
VERCEL_TOKEN=<your-vercel-authentication-token>
ORG_ID=<your-vercel-organization-id>
PROJECT_ID=<your-vercel-project-id>
```

### Google Cloud Configuration

```
GCP_PROJECT_ID=<your-gcp-project-id>
GCP_REGION=us-central1
WIF_PROVIDER=<workload-identity-federation-provider>
WIF_SERVICE_ACCOUNT=<service-account-email>
```

### Database Configuration

```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>?sslmode=require
REDIS_URL=redis://<host>:<port>/<database>
```

### Earth Engine Configuration

```
GEE_SERVICE_ACCOUNT_FILE=<json-key-content-base64-encoded>
GEE_PROJECT_ID=<your-gee-project-id>
```

## Setup Instructions

### 1. Google Cloud Setup

```bash
# Create GCP project
gcloud projects create aurora-osi-v3 --name="Aurora OSI v3"
gcloud config set project aurora-osi-v3

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com

# Create service account
gcloud iam service-accounts create aurora-backend \
  --display-name="Aurora Backend Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding aurora-osi-v3 \
  --member=serviceAccount:aurora-backend@aurora-osi-v3.iam.gserviceaccount.com \
  --role=roles/run.invoker

gcloud projects add-iam-policy-binding aurora-osi-v3 \
  --member=serviceAccount:aurora-backend@aurora-osi-v3.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

### 2. Workload Identity Federation Setup

```bash
# Create workload identity pool
gcloud iam workload-identity-pools create github \
  --project aurora-osi-v3 \
  --location=global \
  --display-name="GitHub"

# Create workload identity provider
gcloud iam workload-identity-pools providers create-oidc github \
  --project aurora-osi-v3 \
  --location=global \
  --workload-identity-pool=github \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri=https://token.actions.githubusercontent.com

# Grant permissions to GitHub repo
gcloud iam service-accounts add-iam-policy-binding aurora-backend@aurora-osi-v3.iam.gserviceaccount.com \
  --project aurora-osi-v3 \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/tulwegroup/aurora-githubpages"
```

### 3. Database Setup (Cloud SQL)

```bash
# Create PostgreSQL instance
gcloud sql instances create aurora-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=<secure-password>

# Create database
gcloud sql databases create aurora_osi_v3 --instance=aurora-db

# Create user
gcloud sql users create aurora_user \
  --instance=aurora-db \
  --password=<secure-password>
```

### 4. Redis Setup (Memorystore)

```bash
# Create Redis instance
gcloud redis instances create aurora-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=7.0
```

### 5. GitHub Repository Setup

```bash
# Clone repository
git clone https://github.com/tulwegroup/aurora-githubpages.git
cd aurora-githubpages

# Add secrets
gh secret set VERCEL_TOKEN --body "your-token"
gh secret set ORG_ID --body "your-org-id"
gh secret set PROJECT_ID --body "your-project-id"
gh secret set GCP_PROJECT_ID --body "aurora-osi-v3"
gh secret set WIF_PROVIDER --body "your-provider-uri"
gh secret set WIF_SERVICE_ACCOUNT --body "aurora-backend@aurora-osi-v3.iam.gserviceaccount.com"
gh secret set DATABASE_URL --body "postgresql://..."
gh secret set REDIS_URL --body "redis://..."
```

## Verification

```bash
# Test deployment workflow
gh workflow run deploy.yml --ref main

# Monitor deployment
gh run list --workflow=deploy.yml

# Check Cloud Run service
gcloud run services describe aurora-backend --region us-central1

# View logs
gcloud run services logs read aurora-backend --region us-central1 --limit=50
```

## Rollback Procedures

```bash
# Rollback to previous Cloud Run revision
gcloud run services update-traffic aurora-backend \
  --region us-central1 \
  --to-revisions LATEST=0,PREVIOUS=100

# Revert frontend on Vercel
# Use Vercel dashboard: Settings > Deployments > Rollback
```

## Monitoring

- **Backend Logs**: `gcloud run services logs read aurora-backend --region us-central1`
- **Cloud Run Dashboard**: https://console.cloud.google.com/run
- **Vercel Deployments**: https://vercel.com/dashboard
- **GitHub Actions**: https://github.com/tulwegroup/aurora-githubpages/actions
