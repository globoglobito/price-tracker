# Price Tracker

A comprehensive price tracking application built with modern DevOps practices, designed specifically for WSL2 + MicroK8s environments.

## 🏗️ Architecture

- **Frontend**: TBD (React/Vue.js planned)  
- **Backend**: TBD (Node.js/Python planned)
- **Database**: PostgreSQL (Bitnami Helm chart)
- **Container Registry**: Docker Hub
- **Orchestration**: Kubernetes (MicroK8s)
- **CI/CD**: GitHub Actions
- **Environment**: WSL2 + Ubuntu

## 🚀 Quick Start (Fresh WSL2 Environment)

### 1. Prerequisites Setup
```bash
# Update WSL2 system
sudo apt update && sudo apt upgrade -y

# Install MicroK8s
sudo snap install microk8s --classic

# Enable required addons
microk8s enable dns storage

# Add user to microk8s group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
newgrp microk8s

# Verify installation
microk8s status --wait-ready
```

### 2. **CRITICAL: Create Secrets First**
Before deploying anything, you must create all required Kubernetes secrets:

📖 **[Follow the complete secrets setup guide](docs/SECRETS.md)**

Quick commands (replace with your actual values):
```bash
# Create namespace
kubectl create namespace price-tracker

# Create all 4 required secrets (see docs/SECRETS.md for details)
kubectl create secret generic postgres-secret --from-literal=POSTGRES_USER=price_tracker_user --from-literal=POSTGRES_PASSWORD=your_password --from-literal=POSTGRES_DB=price_tracker_db -n price-tracker
kubectl create secret generic app-secrets --from-literal=DATABASE_URL=postgresql://price_tracker_user:your_password@postgres-service:5432/price_tracker_db --from-literal=JWT_SECRET=$(openssl rand -base64 32) --from-literal=API_KEY=placeholder -n price-tracker
kubectl create secret docker-registry docker-registry-secret --docker-server=https://index.docker.io/v1/ --docker-username=your_username --docker-password=your_password --docker-email=your_email -n price-tracker
kubectl create secret generic price-tracker-postgres-credentials --from-literal=postgres-password=your_password --from-literal=password=your_password -n price-tracker
```

### 3. Deploy Infrastructure
```bash
# Clone repository
git clone https://github.com/globoglobito/price-tracker.git
cd price-tracker

# Make scripts executable
chmod +x scripts/*.sh tests/*.sh

# Deploy all infrastructure
./scripts/deploy.sh
```

### 4. Verify Deployment
```bash
# Run comprehensive integration tests
./tests/run-tests.sh

# Check deployment status
kubectl get all -n price-tracker

# Access application (when ready)
kubectl port-forward service/price-tracker-service 8080:80 -n price-tracker
```

## 🧪 Testing

We provide comprehensive integration tests to validate your infrastructure:

```bash
# Test WSL2 environment only
./tests/run-tests.sh wsl2

# Test without requiring deployment
./tests/run-tests.sh --skip-deploy

# Full infrastructure testing
./tests/run-tests.sh
```

Test suites include:
- **WSL2 Environment**: MicroK8s, storage, networking
- **CI/CD Pipeline**: GitHub Actions, Docker builds
- **Infrastructure**: K8s deployments, secrets, services
- **Database**: PostgreSQL connectivity, performance

## 📁 Project Structure

```
price-tracker/
├── .github/workflows/     # GitHub Actions CI/CD
├── docs/                  # Documentation
│   └── SECRETS.md        # Secrets setup guide
├── helm/                  # Helm chart values
├── k8s/                   # Kubernetes manifests
│   ├── secrets.yaml      # Secret templates (for reference)
│   ├── configmaps.yaml   # Application configuration
│   ├── deployment.yaml   # Main application deployment
│   ├── service.yaml      # Kubernetes services
│   └── manifests/        # Alternative deployment configs
├── scripts/               # Deployment and utility scripts
├── tests/                 # Integration test suites
└── CHANGELOG.md          # Version history
```

## 🔐 Security Features

- **No Hardcoded Secrets**: All credentials via K8s secrets
- **Non-root Containers**: Security contexts for all deployments
- **Resource Limits**: Memory and CPU constraints
- **Image Pull Secrets**: Secure Docker Hub access
- **Network Policies**: ClusterIP services only

## 🛠️ Development Workflow

### Local Development (WSL2)
```bash
# Start development environment
./scripts/deploy.sh

# Run tests during development
./tests/run-tests.sh --skip-deploy

# View logs
kubectl logs -f deployment/price-tracker -n price-tracker
```

### CI/CD Pipeline
- **Triggers**: Push to main/dev, pull requests
- **Multi-arch Builds**: AMD64 + ARM64 support
- **Docker Hub**: Automated image publishing
- **Caching**: Optimized build times

## 📊 Monitoring & Observability

```bash
# Check application health
kubectl get pods -n price-tracker -w

# View application logs
kubectl logs -f deployment/price-tracker -n price-tracker

# Database logs
kubectl logs -f deployment/postgres -n price-tracker

# Resource usage
kubectl top pods -n price-tracker
```

## 🔄 Common Operations

### Update Application
```bash
# Pull latest changes
git pull origin main

# Redeploy
kubectl rollout restart deployment/price-tracker -n price-tracker

# Monitor rollout
kubectl rollout status deployment/price-tracker -n price-tracker
```

### Backup Database
```bash
# Create backup
kubectl exec deployment/postgres -n price-tracker -- pg_dump -U price_tracker_user price_tracker_db > backup.sql

# Restore backup
kubectl exec -i deployment/postgres -n price-tracker -- psql -U price_tracker_user -d price_tracker_db < backup.sql
```

### Scale Application
```bash
# Scale up
kubectl scale deployment price-tracker --replicas=3 -n price-tracker

# Scale down
kubectl scale deployment price-tracker --replicas=1 -n price-tracker
```

## 🐛 Troubleshooting

### Common Issues

1. **Secrets not found**: Ensure all 4 secrets are created (see [docs/SECRETS.md](docs/SECRETS.md))
2. **Pods pending**: Check storage and resource availability
3. **Image pull errors**: Verify Docker Hub credentials in `docker-registry-secret`
4. **Database connection**: Check PostgreSQL pod status and secrets

### Useful Commands
```bash
# Debug pod issues
kubectl describe pod <pod-name> -n price-tracker

# Check secret contents
kubectl get secret postgres-secret -n price-tracker -o yaml

# Reset deployment
kubectl delete namespace price-tracker
# Then recreate secrets and redeploy
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run integration tests: `./tests/run-tests.sh`
5. Submit a pull request

## 📖 Documentation

- **[Secrets Setup Guide](docs/SECRETS.md)** - Complete secrets configuration
- **[Integration Tests](tests/README.md)** - Testing documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## 📄 License

This project is licensed under the MIT License.

## 🙋‍♂️ Support

For issues and questions:
1. Check the troubleshooting section above
2. Run integration tests to identify issues
3. Open a GitHub issue with test results
