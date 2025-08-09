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
- **Database**: PostgreSQL with comprehensive schema supporting any website
- **Container Registry**: Docker Hub
- **Orchestration**: Kubernetes (MicroK8s)
- **CI/CD**: GitHub Actions
- **Environment**: WSL2 + Ubuntu
- **Python**: 3.12+ with virtual environment

### Database Schema
- **Comprehensive Design**: Single table handles all websites (eBay, Reverb, ShopGoodwill, etc.)
- **Maximum Flexibility**: No restrictive constraints - supports any website, condition, or currency
- **Rich Data Support**: Condition, shipping, auctions, location, currency, and more
- **Future-Proof**: Ready for any new website without schema changes

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

### 4. Deploy Complete System
```bash
# Deploy everything (database + API) with comprehensive testing
./scripts/deploy-complete.sh
```

### 5. Verify Deployment
```bash
# Run comprehensive integration tests
./database/test_integration.sh && ./api/test_api_integration.sh

# Check deployment status
kubectl get all -n price-tracker

# Access applications
# - Search API: http://localhost:30080/health
# - API Documentation: http://localhost:30080/docs
```

## 🧪 Testing & Local Development

### Local Development
```bash
# All components run in Kubernetes (MicroK8s)
# No local development needed - everything is containerized

# View logs and monitor the system
kubectl logs -f deployment/price-tracker-api -n price-tracker
kubectl logs -f deployment/postgres -n price-tracker

# Access the API directly
curl http://localhost:30080/health
```

### Integration Testing
We provide essential integration tests to validate your deployment:

```bash
# Run essential tests to verify deployment
./database/test_integration.sh && ./api/test_api_integration.sh
```

Tests verify:
- **Database**: Schema, tables, constraints, data operations (20 tests)
- **API**: Health endpoints, CRUD operations, error handling (15 tests)
- **Integration**: Full system connectivity and functionality

## 📁 Project Structure

```
price-tracker/
├── .github/workflows/     # GitHub Actions CI/CD
├── docs/                  # Documentation
│   └── SECRETS.md        # Secrets setup guide
├── scripts/               # Deployment and utility scripts
│   ├── deploy-complete.sh # Complete deployment script
│   ├── clean-slate-deploy.sh # Clean slate deployment
│   └── setup-secrets.sh  # Interactive secrets setup
├── k8s/                   # Kubernetes manifests
│   ├── api-deployment.yaml # API deployment
│   ├── api-service.yaml   # API service
│   ├── postgres-values.yaml # PostgreSQL configuration
│   └── manifests/        # Deployment configs
│       └── db-deployment.yaml  # Database deployment
├── database/              # Database schema and tests
│   ├── migrations/       # Database migrations
│   │   └── 001_complete_schema.sql # Comprehensive schema
│   ├── test_integration.sh # Database integration tests
│   └── README.md         # Database documentation
├── api/                   # FastAPI Search API
│   ├── test_api_integration.sh # API integration tests
│   └── README.md         # API documentation
├── tests/                 # Test documentation
│   └── README.md         # Integration testing guide
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
./scripts/deploy-complete.sh

# Run tests during development
./database/test_integration.sh && ./api/test_api_integration.sh

# View logs
kubectl logs -f deployment/price-tracker-api -n price-tracker
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
4. Run integration tests: `./database/test_integration.sh` and `./api/test_api_integration.sh`
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
