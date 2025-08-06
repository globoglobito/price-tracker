#!/bin/bash
# Complete deployment script for Price Tracker
# Deploys database, API, and runs tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Use microk8s kubectl
KUBECTL="microk8s kubectl"

echo -e "${BLUE}🚀 Complete Price Tracker Deployment${NC}"
echo "====================================="

# Step 1: Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
if ! $KUBECTL cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ Kubernetes cluster not accessible${NC}"
    exit 1
fi

if ! microk8s status --wait-ready >/dev/null 2>&1; then
    echo -e "${RED}❌ MicroK8s not ready${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Step 2: Check and create namespace
echo -e "${YELLOW}📁 Checking namespace...${NC}"
if ! $KUBECTL get namespace price-tracker &>/dev/null; then
    echo -e "${YELLOW}📁 Creating price-tracker namespace...${NC}"
    $KUBECTL create namespace price-tracker
    echo -e "${GREEN}✅ Namespace created${NC}"
else
    echo -e "${GREEN}✅ Namespace already exists${NC}"
fi

# Step 3: Check secrets
echo -e "${YELLOW}🔐 Checking secrets...${NC}"
if ! $KUBECTL get secret postgres-secret -n price-tracker &>/dev/null; then
    echo -e "${RED}❌ Secrets not found. Please run: ./scripts/setup-secrets.sh${NC}"
    exit 1
fi

if ! $KUBECTL get secret docker-registry-secret -n price-tracker &>/dev/null; then
    echo -e "${RED}❌ Docker registry secret not found. Please run: ./scripts/setup-secrets.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Secrets found${NC}"

# Step 4: Deploy database
echo -e "${YELLOW}🗄️  Deploying database...${NC}"
$KUBECTL apply -f k8s/configmaps.yaml -n price-tracker
$KUBECTL apply -f k8s/postgres-values.yaml -n price-tracker
$KUBECTL apply -f k8s/manifests/db-deployment.yaml -n price-tracker

# Verify database deployment was created
if ! $KUBECTL get deployment postgres -n price-tracker &>/dev/null; then
    echo -e "${RED}❌ Database deployment failed to create${NC}"
    exit 1
fi

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
$KUBECTL wait --for=condition=ready pod -l app=postgres -n price-tracker --timeout=300s
echo -e "${GREEN}✅ Database ready${NC}"

# Step 5: Apply database migration
echo -e "${YELLOW}📝 Applying database migration...${NC}"
./database/apply_migration.sh
echo -e "${GREEN}✅ Database migration applied${NC}"

# Step 6: Deploy API
echo -e "${YELLOW}🚀 Deploying API...${NC}"
$KUBECTL apply -f k8s/api-deployment.yaml -n price-tracker
$KUBECTL apply -f k8s/api-service.yaml -n price-tracker

# Verify API deployment was created
if ! $KUBECTL get deployment price-tracker-api -n price-tracker &>/dev/null; then
    echo -e "${RED}❌ API deployment failed to create${NC}"
    exit 1
fi

# Wait for API to be ready
echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
$KUBECTL wait --for=condition=ready pod -l app=price-tracker-api -n price-tracker --timeout=300s
echo -e "${GREEN}✅ API ready${NC}"

# Step 7: Run integration tests
echo -e "${YELLOW}🧪 Running integration tests...${NC}"
./database/test_integration.sh

# Step 8: Test API endpoints
echo -e "${YELLOW}🔍 Testing API endpoints...${NC}"
sleep 10  # Give API time to fully start

# Get API service URL
API_URL="http://localhost:30080"

# Test health endpoint
if curl -f "${API_URL}/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    exit 1
fi

# Test search endpoints
if curl -f "${API_URL}/searches" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ API search endpoint working${NC}"
else
    echo -e "${RED}❌ API search endpoint failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Complete deployment successful!${NC}"
echo "====================================="
echo -e "${BLUE}📊 Services:${NC}"
echo "  - Database: PostgreSQL (price-tracker namespace)"
echo "  - API: FastAPI Search API (port 30080)"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "  - API Health: ${API_URL}/health"
echo "  - API Docs: ${API_URL}/docs"
echo "  - Search Endpoint: ${API_URL}/searches"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  - View pods: $KUBECTL get pods -n price-tracker"
echo "  - View services: $KUBECTL get services -n price-tracker"
echo "  - API logs: $KUBECTL logs -f deployment/price-tracker-api -n price-tracker"
echo "  - Database logs: $KUBECTL logs -f deployment/postgres -n price-tracker" 