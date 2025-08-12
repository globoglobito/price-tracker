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
echo ""

# Use microk8s kubectl for all operations
KUBECTL="microk8s kubectl"

# Check if namespace exists
if ! $KUBECTL get namespace price-tracker &>/dev/null; then
    echo -e "${YELLOW}📁 Creating price-tracker namespace...${NC}"
    $KUBECTL create namespace price-tracker
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



echo ""
echo -e "${YELLOW}🚀 Creating Kubernetes secrets...${NC}"

# Create postgres-secret
echo "Creating postgres-secret..."
$KUBECTL create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=admin \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker



# Create docker-registry-secret
echo "Creating docker-registry-secret..."
$KUBECTL create secret docker-registry docker-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username="$DOCKERHUB_USERNAME" \
  --docker-password="$DOCKERHUB_PASSWORD" \
  --docker-email="$DOCKERHUB_EMAIL" \
  -n price-tracker

# Create price-tracker-postgres-credentials
echo "Creating price-tracker-postgres-credentials..."
$KUBECTL create secret generic price-tracker-postgres-credentials \
  --from-literal=username=admin \
  --from-literal=password="$DB_PASSWORD" \
  -n price-tracker

echo ""
echo -e "${GREEN}✅ All secrets created successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Verification:${NC}"
$KUBECTL get secrets -n price-tracker
echo ""
echo -e "${GREEN}🎉 You can now run: ./scripts/deploy-complete.sh${NC}"