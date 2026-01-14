#!/bin/bash
# Aurora OSI v3 - Google Cloud Run Deployment Script
# This script sets up and deploys Aurora OSI v3 to Google Cloud Run

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"aurora-osi-v3"}
REGION=${2:-"us-central1"}
SERVICE_NAME="aurora-backend"
IMAGE_NAME="${REGION}r.gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${YELLOW}=== Aurora OSI v3 Cloud Run Deployment ===${NC}"
echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"

# Step 1: Authenticate with Google Cloud
echo -e "\n${YELLOW}[1/6] Authenticating with Google Cloud...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}Not authenticated with Google Cloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Step 2: Set project
echo -e "\n${YELLOW}[2/6] Setting GCP project...${NC}"
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✓ Project set${NC}"

# Step 3: Build Docker image
echo -e "\n${YELLOW}[3/6] Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest -f backend.Dockerfile .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built${NC}"
else
    echo -e "${RED}✗ Failed to build Docker image${NC}"
    exit 1
fi

# Step 4: Push to Google Container Registry
echo -e "\n${YELLOW}[4/6] Pushing to Google Container Registry...${NC}"
gcloud auth configure-docker
docker push ${IMAGE_NAME}:latest
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Image pushed to GCR${NC}"
else
    echo -e "${RED}✗ Failed to push image${NC}"
    exit 1
fi

# Step 5: Deploy to Cloud Run
echo -e "\n${YELLOW}[5/6] Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 100 \
    --min-instances 1 \
    --set-env-vars "ENVIRONMENT=production" \
    --port 8000

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
else
    echo -e "${RED}✗ Failed to deploy to Cloud Run${NC}"
    exit 1
fi

# Step 6: Get service URL
echo -e "\n${YELLOW}[6/6] Retrieving service information...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format='value(status.url)')

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}View logs: gcloud run services logs read ${SERVICE_NAME} --region ${REGION}${NC}"
echo -e "${GREEN}Update environment: gcloud run services update ${SERVICE_NAME} --region ${REGION} --set-env-vars KEY=VALUE${NC}"
