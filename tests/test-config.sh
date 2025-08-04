#!/bin/bash
# Shared Test Configuration
# Common configuration and functions used across all test suites

# Default configuration - can be overridden by environment variables
export PROJECT_NAME="${PROJECT_NAME:-price-tracker}"
export NAMESPACE="${NAMESPACE:-price-tracker}"
export DOCKER_REGISTRY="${DOCKER_REGISTRY:-globoglobitos}"
export GITHUB_OWNER="${GITHUB_OWNER:-globoglobito}"

# Function to get dynamic configuration from actual deployments
get_project_config() {
    # Try to get Docker image from deployment files
    if [ -f "k8s/deployment.yaml" ] || [ -f "k8s/manifests/app-deployment.yaml" ]; then
        local image_line=$(grep -h "image:" k8s/deployment.yaml k8s/manifests/app-deployment.yaml 2>/dev/null | head -1)
        if [ -n "$image_line" ]; then
            export DOCKER_IMAGE=$(echo "$image_line" | sed 's/.*image: *\([^[:space:]]*\).*/\1/' | cut -d':' -f1)
        else
            export DOCKER_IMAGE="$DOCKER_REGISTRY/$PROJECT_NAME"
        fi
    else
        export DOCKER_IMAGE="$DOCKER_REGISTRY/$PROJECT_NAME"
    fi
    
    # Try to get GitHub repo from git remote
    if command -v git &> /dev/null && git remote -v &> /dev/null 2>&1; then
        local remote_url=$(git remote get-url origin 2>/dev/null)
        if [ -n "$remote_url" ]; then
            export GITHUB_REPO=$(echo "$remote_url" | sed 's/.*github.com[\/:]\\([^\/]*\/[^\/]*\\)\\(\.git\\)\\?$/\\1/')
        else
            export GITHUB_REPO="$GITHUB_OWNER/$PROJECT_NAME"
        fi
    else
        export GITHUB_REPO="$GITHUB_OWNER/$PROJECT_NAME"
    fi
    
    # Database configuration from actual K8s resources (if available)
    if command -v kubectl &> /dev/null; then
        export DB_NAME=$(kubectl get configmap app-config -n "$NAMESPACE" -o jsonpath='{.data.POSTGRES_DB}' 2>/dev/null || echo "price_tracker_db")
        export DB_USER=$(kubectl get secret postgres-secret -n "$NAMESPACE" -o jsonpath='{.data.POSTGRES_USER}' 2>/dev/null | base64 -d 2>/dev/null || echo "price_tracker_user")
    else
        export DB_NAME="price_tracker_db"
        export DB_USER="price_tracker_user"
    fi
    
    # Standard connection defaults
    export DB_HOST="localhost"
    export DB_PORT="5432"
}

# Function to display current configuration
show_config() {
    echo "📋 Project Configuration:"
    echo "   Project: $PROJECT_NAME"
    echo "   Namespace: $NAMESPACE"
    echo "   Docker Image: $DOCKER_IMAGE"
    echo "   GitHub Repo: $GITHUB_REPO"
    echo "   Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
}

# Function to validate configuration
validate_config() {
    local errors=0
    
    if [ -z "$PROJECT_NAME" ]; then
        echo "❌ PROJECT_NAME is not set"
        errors=$((errors + 1))
    fi
    
    if [ -z "$NAMESPACE" ]; then
        echo "❌ NAMESPACE is not set"
        errors=$((errors + 1))
    fi
    
    if [ -z "$DOCKER_IMAGE" ]; then
        echo "❌ DOCKER_IMAGE is not set"
        errors=$((errors + 1))
    fi
    
    return $errors
}

# Initialize configuration when sourced
get_project_config
