# Price Tracker

A comprehensive price tracking application built with modern DevOps practices, designed specifically for WSL2 + MicroK8s environments.

## 🏗️ Architecture

- **Frontend**: TBD (React/Vue.js planned)  
- **Backend**: Simple Python application (PostgreSQL connectivity demo)
- **Database**: PostgreSQL (Bitnami Helm chart)
- **Container Registry**: Docker Hub
- **Orchestration**: Kubernetes (MicroK8s)
- **CI/CD**: GitHub Actions
- **Environment**: WSL2 + Ubuntu
- **Python**: 3.11+ with virtual environment

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

Quick commands (replace ALL placeholders with your actual values):
```bash
# Create namespace
kubectl create namespace price-tracker

# Create all 4 required secrets (see docs/SECRETS.md for details)
kubectl create secret generic postgres-secret --from-literal=POSTGRES_USER=admin --from-literal=POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD --from-literal=POSTGRES_DB=price_tracker_db -n price-tracker
kubectl create secret generic app-secrets --from-literal=DATABASE_URL=postgresql://admin:YOUR_SECURE_PASSWORD@postgres-service:5432/price_tracker_db --from-literal=JWT_SECRET=$(openssl rand -base64 32) --from-literal=API_KEY=YOUR_API_KEY -n price-tracker
kubectl create secret docker-registry docker-registry-secret --docker-server=https://index.docker.io/v1/ --docker-username=YOUR_DOCKERHUB_USERNAME --docker-password=YOUR_DOCKERHUB_TOKEN --docker-email=YOUR_EMAIL -n price-tracker
kubectl create secret generic price-tracker-postgres-credentials --from-literal=username=admin --from-literal=password=YOUR_SECURE_PASSWORD -n price-tracker

### 3. Setup Python Environment
```bash
# Clone repository
git clone https://github.com/globoglobito/price-tracker.git
cd price-tracker

# Install Python dependencies
sudo apt install python3.12-venv libpq-dev -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh tests/*.sh
```

### 4. Deploy Infrastructure
```bash
# Deploy all infrastructure
./scripts/deploy.sh
```

### 5. Verify Deployment
```bash
# Run comprehensive integration tests
./tests/run-tests.sh

# Check deployment status
kubectl get all -n price-tracker

# Access application (when ready)
kubectl port-forward service/price-tracker-service 8080:80 -n price-tracker
```

## 🧪 Testing & Local Development

### Local Application Testing
```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables for local testing
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=price_tracker_db
export DB_USER=admin
export DB_PASSWORD=YOUR_SECURE_PASSWORD

# Port-forward PostgreSQL for local access
kubectl port-forward service/price-tracker-postgres-postgresql 5432:5432 &

# Run the simple database connectivity test
python app.py
```

### Integration Testing
We provide essential integration tests to validate your deployment:

```bash
# Run essential tests to verify deployment
./tests/run-tests.sh
```

Tests verify:
- **Environment**: MicroK8s running, kubectl connected
- **Deployment**: Namespace, PostgreSQL, and application pods running
- **Database**: PostgreSQL accessible and connectable
- **Application**: Application healthy and running

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
