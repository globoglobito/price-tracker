# Kubernetes Secrets Setup Guide

This document provides complete instructions for creating all required Kubernetes secrets for the Price Tracker application. These secrets must be created manually before deploying the application.

## 📋 Overview

The Price Tracker application requires the following Kubernetes secrets in the `price-tracker` namespace:

- `postgres-secret` (required) – PostgreSQL database credentials
- `docker-registry-secret` (required) – Docker Hub authentication for pulling images
- `rabbitmq-secret` (required) – RabbitMQ message queue credentials
- `price-tracker-postgres-credentials` (optional; only if using Bitnami Helm PostgreSQL)
- `scraper-proxy` (optional) – HTTP/HTTPS proxy for scraper pods if needed
- `kube-prom-stack-grafana` (auto-created) – Grafana admin credentials for monitoring

## 🔧 Prerequisites

- WSL2 with MicroK8s installed and running
- `kubectl` configured to work with MicroK8s
- Base64 encoding capability (`base64` command)

## 🚀 Quick Setup Commands

### 1. Create Namespace
```bash
kubectl create namespace price-tracker
```

### 2. Create Required Secrets
Run these commands in order, replacing the placeholder values with your actual credentials:

```bash
# 1. PostgreSQL Database Secret (required)
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=admin \
  --from-literal=POSTGRES_PASSWORD=your_db_password_here \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker

# 2. Docker Registry Secret (required)
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=your_dockerhub_username \
  --docker-password=your_dockerhub_password \
  --docker-email=your_email@example.com \
  -n price-tracker

# 3. PostgreSQL Credentials for Bitnami Helm Chart (optional)
kubectl create secret generic price-tracker-postgres-credentials \
  --from-literal=postgres-password=your_db_password_here \
  --from-literal=password=your_db_password_here \
  -n price-tracker

# 4. RabbitMQ Secret (required)
kubectl create secret generic rabbitmq-secret \
  --from-literal=username=admin \
  --from-literal=password=admin123 \
  -n price-tracker

# 5. Scraper Proxy (optional)
kubectl create secret generic scraper-proxy \
  --from-literal=http_proxy=http://user:pass@host:port \
  --from-literal=https_proxy=http://user:pass@host:port \
  -n price-tracker
```

## 📝 Detailed Secret Descriptions

### 1. `postgres-secret`
**Purpose**: Core PostgreSQL database credentials used by the application
**Type**: `generic`
**Required Fields**:
- `POSTGRES_USER`: Database username (recommended: `price_tracker_user`)
- `POSTGRES_PASSWORD`: Database password (use a strong password)
- `POSTGRES_DB`: Database name (recommended: `price_tracker_db`)

**Example**:
```bash
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=price_tracker_user \
  --from-literal=POSTGRES_PASSWORD=MySecurePassword123! \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker
```

### 2. `rabbitmq-secret` (required)
**Purpose**: RabbitMQ message queue credentials for the parallel scraping architecture
**Type**: `generic`
**Required Fields**:
- `username`: RabbitMQ username (default: `admin`)
- `password`: RabbitMQ password (default: `admin123`)

**Example**:
```bash
kubectl create secret generic rabbitmq-secret \
  --from-literal=username=admin \
  --from-literal=password=MySecureRabbitMQPassword123! \
  -n price-tracker
```

### 3. `scraper-proxy` (optional)
**Purpose**: Provide outbound proxy settings to the scraper pods when required. This is optional and not needed for most environments.
**Type**: `generic`
**Fields**:
- `http_proxy`: HTTP proxy URL
- `https_proxy`: HTTPS proxy URL

The CronJob references this secret optionally, so you can skip creating it if you do not need a proxy.

### 4. `docker-registry-secret`
**Purpose**: Authentication for pulling Docker images from Docker Hub
**Type**: `docker-registry`
**Required Fields**:
- `--docker-server`: Docker registry URL (use `https://index.docker.io/v1/` for Docker Hub)
- `--docker-username`: Your Docker Hub username
- `--docker-password`: Your Docker Hub password or access token
- `--docker-email`: Your email address

**Example**:
```bash
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=globoglobitos \
  --docker-password=your_dockerhub_password \
  --docker-email=your.email@example.com \
  -n price-tracker
```

### 5. `price-tracker-postgres-credentials`
**Purpose**: Credentials specifically for the Bitnami PostgreSQL Helm chart
**Type**: `generic`
**Required Fields**:
- `postgres-password`: PostgreSQL superuser password (same as POSTGRES_PASSWORD above)
- `password`: Regular user password (same as POSTGRES_PASSWORD above)

**Example**:
```bash
kubectl create secret generic price-tracker-postgres-credentials \
  --from-literal=postgres-password=MySecurePassword123! \
  --from-literal=password=MySecurePassword123! \
  -n price-tracker
```

### 6. `kube-prom-stack-grafana` (Auto-created)
**Purpose**: Grafana admin credentials for monitoring and visualization
**Type**: `generic` (auto-created by observability stack)
**Fields**:
- `admin-password`: Grafana admin password (default: `prom-operator`)
- `admin-user`: Grafana admin username (default: `admin`)

**Access Grafana**:
```bash
# Port forward to access Grafana
kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80

# Access at: http://localhost:3000
# Username: admin
# Password: prom-operator (or get from secret)
kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

## 🔐 Security Best Practices

### Password Generation
Generate strong passwords using these methods:

```bash
# Method 1: OpenSSL (recommended)
openssl rand -base64 24

# Method 2: /dev/urandom
tr -dc A-Za-z0-9 </dev/urandom | head -c 24

# Method 3: pwgen (if installed)
pwgen -s 24 1
```

### JWT Secret Generation
```bash
# Generate a cryptographically secure JWT secret
openssl rand -base64 32
```

## 📋 Verification Commands

After creating all secrets, verify they exist:

```bash
# List all secrets in the namespace
kubectl get secrets -n price-tracker

# Check specific secret contents (base64 encoded)
kubectl get secret postgres-secret -n price-tracker -o yaml
kubectl get secret docker-registry-secret -n price-tracker -o yaml
kubectl get secret price-tracker-postgres-credentials -n price-tracker -o yaml
kubectl get secret scraper-proxy -n price-tracker -o yaml

# Decode a specific secret value
kubectl get secret postgres-secret -n price-tracker -o jsonpath='{.data.POSTGRES_USER}' | base64 -d
```

## 🧪 Testing Secrets

You can test that secrets are working with our integration tests:

```bash
# Test that all secrets exist and are readable
./tests/run-tests.sh --skip-deploy

# Test full deployment including secrets
./scripts/deploy-complete.sh
./tests/run-tests.sh
```

## 🔄 Updating Secrets

To update a secret, delete and recreate it:

```bash
# Delete existing secret
kubectl delete secret postgres-secret -n price-tracker

# Recreate with new values
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=price_tracker_user \
  --from-literal=POSTGRES_PASSWORD=new_password_here \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker

# Restart deployments to pick up new secrets
kubectl rollout restart deployment/postgres -n price-tracker
kubectl rollout restart deployment/price-tracker -n price-tracker
```

## 🚨 Troubleshooting

### Common Issues

1. **Secret not found**:
   ```bash
   # Check if secret exists
   kubectl get secrets -n price-tracker
   
   # Check if namespace exists
   kubectl get namespaces | grep price-tracker
   ```

2. **Permission denied**:
   ```bash
   # Check if MicroK8s is running
   microk8s status
   
   # Use microk8s kubectl if regular kubectl doesn't work
   microk8s kubectl get secrets -n price-tracker
   ```

3. **Base64 decoding issues**:
   ```bash
   # Some systems need -d flag, others need -D
   echo "dGVzdA==" | base64 -d  # Linux
   echo "dGVzdA==" | base64 -D  # macOS
   ```

4. **Missing secret keys**:
   ```bash
   # Check what keys exist in a secret
   kubectl describe secret rabbitmq-secret -n price-tracker
   
   # If rabbitmq-secret is missing username key, add it:
   kubectl patch secret rabbitmq-secret -n price-tracker --type='json' -p='[{"op": "add", "path": "/data/username", "value": "YWRtaW4="}]'
   
   # Or recreate the secret with both keys:
   kubectl delete secret rabbitmq-secret -n price-tracker
   kubectl create secret generic rabbitmq-secret \
     --from-literal=username=admin \
     --from-literal=password=admin123 \
     -n price-tracker
   ```

## 📁 Template Files

For convenience, you can save this template and fill in your values:

### `create-secrets.sh` (Template)
```bash
#!/bin/bash
# Price Tracker Secrets Creation Script
# Fill in your actual values below

set -e

# Configuration - CHANGE THESE VALUES
DB_PASSWORD="your_db_password_here"
JWT_SECRET="$(openssl rand -base64 32)"
API_KEY="your_api_key_here"
DOCKERHUB_USERNAME="your_dockerhub_username"
DOCKERHUB_PASSWORD="your_dockerhub_password"
DOCKERHUB_EMAIL="your_email@example.com"

echo "Creating Price Tracker secrets..."

# Create namespace
kubectl create namespace price-tracker --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=price_tracker_user \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --from-literal=POSTGRES_DB=price_tracker_db \
  -n price-tracker

kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL="postgresql://price_tracker_user:$DB_PASSWORD@postgres-service:5432/price_tracker_db" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=API_KEY="$API_KEY" \
  -n price-tracker

kubectl create secret docker-registry docker-registry-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username="$DOCKERHUB_USERNAME" \
  --docker-password="$DOCKERHUB_PASSWORD" \
  --docker-email="$DOCKERHUB_EMAIL" \
  -n price-tracker

kubectl create secret generic price-tracker-postgres-credentials \
  --from-literal=postgres-password="$DB_PASSWORD" \
  --from-literal=password="$DB_PASSWORD" \
  -n price-tracker

echo "✅ All secrets created successfully!"
echo "🔍 Verifying secrets..."
kubectl get secrets -n price-tracker
```

## 🎯 Integration with Deployment

These secrets are automatically used by:
- `k8s/api-deployment.yaml` - FastAPI application deployment
- `k8s/rabbitmq-deployment.yaml` - RabbitMQ message queue deployment
- `k8s/collector-job.yaml` - Collector job for search results
- `k8s/worker-job.yaml` - Worker jobs for parallel enrichment
- `k8s/manifests/db-deployment.yaml` - Database deployment
- `helm/price-tracker-postgres-values.yaml` - Helm chart values

Create at least the required secrets before running `./scripts/deploy-complete.sh`. The `scraper-proxy` and `price-tracker-postgres-credentials` are optional depending on your setup.
