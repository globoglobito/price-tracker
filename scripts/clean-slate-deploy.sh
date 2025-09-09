#!/bin/bash
# Clean slate deployment script for Price Tracker
# Removes everything and redeploys from scratch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Use microk8s kubectl
KUBECTL="microk8s kubectl"

echo -e "${BLUE}🧹 Clean Slate Deployment for Price Tracker${NC}"
echo "============================================="

# Step 1: Clean up existing resources
echo -e "${YELLOW}🧹 Cleaning up existing resources...${NC}"

# Delete API resources
$KUBECTL delete deployment price-tracker-api -n price-tracker --ignore-not-found=true
$KUBECTL delete service price-tracker-api-service -n price-tracker --ignore-not-found=true

# Delete old app resources
$KUBECTL delete deployment price-tracker-app -n price-tracker --ignore-not-found=true
$KUBECTL delete service price-tracker-service -n price-tracker --ignore-not-found=true
$KUBECTL delete service price-tracker-api-service -n price-tracker --ignore-not-found=true

# Delete database resources
$KUBECTL delete deployment postgres -n price-tracker --ignore-not-found=true
$KUBECTL delete service postgres-service -n price-tracker --ignore-not-found=true
$KUBECTL delete pvc postgres-pvc -n price-tracker --ignore-not-found=true

# Delete configmaps (but keep secrets)
$KUBECTL delete configmap postgres-config -n price-tracker --ignore-not-found=true

echo -e "${YELLOW}⚠️  Note: Secrets are preserved. If you want to recreate them, run: ./scripts/setup-secrets.sh${NC}"

# Wait for cleanup
echo -e "${YELLOW}⏳ Waiting for cleanup to complete...${NC}"
sleep 10

echo -e "${GREEN}✅ Cleanup completed${NC}"

# Step 2: Run complete deployment
echo -e "${YELLOW}🚀 Starting complete deployment...${NC}"
./scripts/deploy-complete.sh

echo ""
echo -e "${GREEN}🎉 Clean slate deployment completed!${NC}"
echo "=============================================" 