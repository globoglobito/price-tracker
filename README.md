# Price Tracker

A comprehensive price tracking application built with modern DevOps practices, designed specifically for WSL2 + MicroK8s environments.

## 🏗️ Architecture

### Image Strategy
- **Database**: `postgres:15-alpine` (official PostgreSQL image)
- **API**: `globoglobitos/price-tracker-api:latest` (custom FastAPI application)
- **Future Scrapers**: `globoglobitos/price-tracker-scraper:latest` (custom scraper pods)

### Components
- **Frontend**: TBD (React/Vue.js planned)  
- **Backend**: FastAPI Search API (PostgreSQL connectivity)
- **Database**: PostgreSQL (official image with custom schema)
- **Container Registry**: Docker Hub
- **Orchestration**: Kubernetes (MicroK8s)
- **CI/CD**: GitHub Actions
- **Environment**: WSL2 + Ubuntu
- **Python**: 3.12+ with virtual environment

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

# Create kubectl alias (recommended for easier usage)
sudo snap alias microk8s.kubectl kubectl

# Verify kubectl works
kubectl cluster-info
```

### 2. **🔐 Setup Secrets (Interactive)**
Before deploying, you need to create Kubernetes secrets. We provide an interactive script to make this easy:

```bash
# Run the interactive secrets setup script
./scripts/setup-secrets.sh
```

The script will prompt you for:
- **Database password** (required)
- **Docker Hub credentials** (username, password/token, email)

📖 **[For manual setup, see the complete secrets guide](docs/SECRETS.md)**

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

### 5. Deploy Search API (Optional)
```bash
# Deploy the FastAPI Search API (images built via GitHub Actions)
microk8s kubectl apply -f k8s/api-deployment.yaml
microk8s kubectl apply -f k8s/api-service.yaml
```

### 6. Verify Deployment
```bash
# Run comprehensive integration tests
./database/test_integration.sh

# Check deployment status
kubectl get all -n price-tracker

# Access applications
# - Original app: kubectl port-forward service/price-tracker-service 8080:80 -n price-tracker
# - Search API: http://localhost:30080/health
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
kubectl port-forward service/postgres-service 5432:5432 -n price-tracker &

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
├── scripts/               # Deployment and utility scripts
│   ├── deploy.sh         # Main deployment script
│   └── setup-secrets.sh  # Interactive secrets setup
├── helm/                  # Helm chart values
├── k8s/                   # Kubernetes manifests
│   ├── configmaps.yaml   # Application configuration
│   ├── postgres-values.yaml # PostgreSQL configuration
│   ├── service.yaml      # Kubernetes services
│   └── manifests/        # Deployment configs
│       ├── app-deployment.yaml # Application deployment
│       └── db-deployment.yaml  # Database deployment
├── tests/                 # Integration test suites
│   ├── run-tests.sh      # Main test runner
│   └── test-simple.sh    # Simple test suite
├── app.py                 # Main Python application
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
└── CHANGELOG.md          # Version history
```

## 🔐 Security Features

- **No Hardcoded Secrets**: All credentials via K8s secrets
- **Interactive Setup**: Secure secrets creation with `./scripts/setup-secrets.sh`
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
kubectl logs -f deployment/price-tracker-app -n price-tracker
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

# View API logs
kubectl logs -f deployment/price-tracker-api -n price-tracker

# Database logs
kubectl logs -f deployment/postgres -n price-tracker

# Resource usage
kubectl top pods -n price-tracker
```

## 🔄 Common Operations

### Complete Deployment (Recommended)
```bash
# Clean slate deployment - removes everything and redeploys
./scripts/clean-slate-deploy.sh

# Or step-by-step deployment
./scripts/deploy-complete.sh
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Redeploy API
kubectl rollout restart deployment/price-tracker-api -n price-tracker

# Monitor rollout
kubectl rollout status deployment/price-tracker-api -n price-tracker
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
# Scale up API
kubectl scale deployment price-tracker-api --replicas=3 -n price-tracker

# Scale down API
kubectl scale deployment price-tracker-api --replicas=1 -n price-tracker
```

## 🐛 Troubleshooting

### Common Issues

1. **kubectl not found/connection refused**: Make sure you've created the alias with `sudo snap alias microk8s.kubectl kubectl` or use `microk8s kubectl` instead
2. **Secrets not found**: Ensure all 4 secrets are created (see [docs/SECRETS.md](docs/SECRETS.md))
3. **Pods pending**: Check storage and resource availability
4. **Image pull errors**: Verify Docker Hub credentials in `docker-registry-secret`. API image: `globoglobitos/price-tracker-api:latest`
5. **Database connection**: Check PostgreSQL pod status and secrets

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
