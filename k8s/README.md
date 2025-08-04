# Kubernetes Deployment Guide

This directory contains all the Kubernetes manifests and configurations needed to deploy the Price Tracker application on MicroK8s.

## Prerequisites

1. **MicroK8s installed and running**:
   ```bash
   # Install MicroK8s (Ubuntu/Debian)
   sudo snap install microk8s --classic
   
   # Enable required addons
   microk8s enable dns storage helm3
   
   # Create alias for kubectl (optional)
   sudo snap alias microk8s.kubectl kubectl
   ```

2. **Helm (if using Bitnami PostgreSQL chart)**:
   ```bash
   # Add Bitnami repository
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
   ```

## Deployment Options

### Option 1: Using Helm for PostgreSQL (Recommended)

1. **Deploy PostgreSQL using Helm**:
   ```bash
   helm install price-tracker-postgres bitnami/postgresql \
     -f helm/price-tracker-postgres-values.yaml \
     --namespace default
   ```

2. **Deploy the application**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

### Option 2: Using Pure Kubernetes Manifests

Run the deployment script:
```bash
# WSL2/Linux (Bash)
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Or deploy manually:
```bash
# Create Docker Hub secret first
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=docker.io \
  --docker-username=globoglobitos \
  --docker-password=YOUR_DOCKER_HUB_TOKEN

# Apply in order
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/postgres-values.yaml
kubectl apply -f k8s/manifests/db-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Option 3: Using Kustomize

```bash
kubectl apply -k k8s/
```

## File Structure

```
k8s/
├── deployment.yaml              # Main application deployment
├── service.yaml                 # Application service
├── secrets.yaml                 # Database credentials
├── configmaps.yaml             # Database init scripts
├── postgres-values.yaml        # PostgreSQL config (K8s native)
├── kustomization.yaml          # Kustomize configuration
└── manifests/
    ├── app-deployment.yaml     # Alternative app deployment
    └── db-deployment.yaml      # PostgreSQL deployment (K8s native)

helm/
└── price-tracker-postgres-values.yaml  # Helm values for PostgreSQL

scripts/
├── deploy.sh                   # Bash deployment script
└── helm-commands.sh            # Helm command examples
```

## Configuration

### Database Configuration

The database is configured with:
- **Database**: `price_tracker_db`
- **User**: `price_tracker_user`
- **Password**: `price_tracker_password` (stored in secrets)
- **Storage**: 8Gi persistent volume using `microk8s-hostpath`

### Application Configuration

Environment variables:
- `DB_HOST`: Database service hostname
- `DB_PORT`: Database port (5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username (from secret)
- `DB_PASSWORD`: Database password (from secret)
- `ENVIRONMENT`: deployment environment (development)
- `LOG_LEVEL`: Application log level (INFO)
- `SCRAPE_INTERVAL`: Scraping interval in seconds (3600)

## Accessing the Application

1. **Check deployment status**:
   ```bash
   kubectl get pods,services,pvc -l project=price-tracker
   ```

2. **Port forward to access the application**:
   ```bash
   kubectl port-forward service/price-tracker-service 8080:80
   ```

3. **Access at**: `http://localhost:8080`

## Database Access

1. **Using kubectl exec**:
   ```bash
   kubectl exec -it deployment/postgres -- psql -U price_tracker_user -d price_tracker_db
   ```

2. **Port forward for external access**:
   ```bash
   kubectl port-forward service/postgres-service 5432:5432
   # Then connect using: psql -h localhost -p 5432 -U price_tracker_user -d price_tracker_db
   ```

## Monitoring and Troubleshooting

1. **View application logs**:
   ```bash
   kubectl logs -f deployment/price-tracker
   ```

2. **View database logs**:
   ```bash
   kubectl logs -f deployment/postgres
   ```

3. **Check resource usage**:
   ```bash
   kubectl top pods
   ```

4. **Describe resources for troubleshooting**:
   ```bash
   kubectl describe pod <pod-name>
   kubectl describe service <service-name>
   ```

## Cleanup

To remove all resources:
```bash
# Manually cleanup
kubectl delete all -l project=price-tracker
kubectl delete secrets -l project=price-tracker
kubectl delete configmaps -l project=price-tracker
kubectl delete pvc -l app=postgres

# If using Helm for PostgreSQL
helm uninstall price-tracker-postgres
```

## Security Notes

⚠️ **Important**: This configuration uses hardcoded passwords for development purposes. In production:

1. Use proper secret management (e.g., Sealed Secrets, External Secrets)
2. Enable TLS/SSL for database connections
3. Use network policies to restrict traffic
4. Implement proper RBAC
5. Use non-root containers
6. Scan images for vulnerabilities

## Next Steps

1. Add monitoring with Prometheus and Grafana
2. Implement proper logging with Fluentd or Loki
3. Add ingress controller for external access
4. Set up backup strategies for the database
5. Implement autoscaling based on metrics
