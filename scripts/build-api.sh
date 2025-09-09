#!/bin/bash
# Build and push the Price Tracker API Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
IMAGE_NAME="globoglobitos/price-tracker-api"
TAG="latest"

echo -e "${BLUE}🐳 Building Price Tracker API Docker Image${NC}"
echo "====================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push the image
echo -e "${YELLOW}📤 Pushing Docker image to registry...${NC}"
docker push ${IMAGE_NAME}:${TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image pushed successfully${NC}"
else
    echo -e "${RED}❌ Docker push failed${NC}"
    echo -e "${YELLOW}💡 Make sure you're logged in to Docker Hub: docker login${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 API Docker image ready for deployment!${NC}"
echo "====================================="
echo "Image: ${IMAGE_NAME}:${TAG}"
echo "Ready to deploy with: kubectl apply -f k8s/api-deployment.yaml" 