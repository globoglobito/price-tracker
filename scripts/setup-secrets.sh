#!/bin/bash
# Interactive Secrets Setup Script for Price Tracker
# This script prompts for credentials and creates all required Kubernetes secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}🔐 Price Tracker Secrets Setup${NC}"
echo "====================================="
echo ""
echo "This script will help you create all required Kubernetes secrets."
echo "You'll be prompted for the following information:"
echo "  - Database password"
echo "  - Docker Hub credentials (username, password/token, email)"
echo "  - API key (optional)"
echo "  - JWT secret (auto-generated if not provided)"
echo ""

# Check if namespace exists
if ! kubectl get namespace price-tracker &>/dev/null; then
    echo -e "${YELLOW}📁 Creating price-tracker namespace...${NC}"
    kubectl create namespace price-tracker
    echo -e "${GREEN}✅ Namespace created${NC}"
else
    echo -e "${GREEN}✅ Namespace already exists${NC}"
fi

echo ""

# Prompt for database password
read -s -p "Enter database password: " DB_PASSWORD
echo ""
read -s -p "Confirm database password: " DB_PASSWORD_CONFIRM
echo ""

if [ "$DB_PASSWORD" != "$DB_PASSWORD_CONFIRM" ]; then
    echo -e "${RED}❌ Passwords don't match. Exiting.${NC}"
    exit 1
fi

# Prompt for Docker Hub credentials
echo ""
echo -e "${YELLOW}🐳 Docker Hub Credentials${NC}"
read -p "Docker Hub username: " DOCKERHUB_USERNAME
read -s -p "Docker Hub password/token: " DOCKERHUB_PASSWORD
echo ""
read -p "Docker Hub email: " DOCKERHUB_EMAIL

# Prompt for API key (optional)
echo ""
echo -e "${YELLOW}🔑 API Key (optional)${NC}"
read -p "API key (press Enter to use 'test-api-key-123'): " API_KEY
API_KEY=${API_KEY:-"test-api-key-123"}

# Generate JWT secret if not provided
echo ""
echo -e "${YELLOW}🔐 JWT Secret${NC}"
read -p "JWT secret (press Enter to auto-generate): " JWT_SECRET
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -base64 32)
    echo -e "${GREEN}✅ Auto-generated JWT secret${NC}"
fi

echo ""
echo -e "${YELLOW}🚀 Creating Kubernetes secrets...${NC}"

# Create postgres-secret
echo "Creating postgres-secret..."
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=admin \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker

# Create app-secrets
echo "Creating app-secrets..."
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL="postgresql://admin:$DB_PASSWORD@postgres-service:5432/price_tracker_db" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=API_KEY="$API_KEY" \
  -n price-tracker

# Create docker-registry-secret
echo "Creating docker-registry-secret..."
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username="$DOCKERHUB_USERNAME" \
  --docker-password="$DOCKERHUB_PASSWORD" \
  --docker-email="$DOCKERHUB_EMAIL" \
  -n price-tracker

# Create price-tracker-postgres-credentials
echo "Creating price-tracker-postgres-credentials..."
kubectl create secret generic price-tracker-postgres-credentials \
  --from-literal=username=admin \
  --from-literal=password="$DB_PASSWORD" \
  -n price-tracker

echo ""
echo -e "${GREEN}✅ All secrets created successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Verification:${NC}"
kubectl get secrets -n price-tracker
echo ""
echo -e "${GREEN}🎉 You can now run: ./scripts/deploy.sh${NC}" 