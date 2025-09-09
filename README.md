# Price Tracker

An end-to-end price tracking app for musical instruments (e.g., saxophones), built to teach hands-on Kubernetes on WSL2, scraping with Playwright, and a lean Postgres-backed API. This README is a step-by-step guide so anyone can get it running.

## Who this is for
- You’re on WSL2 and want a realistic microservice + Kubernetes project.
- You want a scraper that avoids bot detection with human-like behavior.
- You prefer a single repo you can run locally with MicroK8s.

## What you'll deploy
- PostgreSQL (schema + migrations) in MicroK8s
- FastAPI (read-only) Search API on NodePort 30080
- RabbitMQ message queue for distributed processing
- **Collector Job**: Scrapes eBay search results and queues listings for enrichment
- **Worker Jobs**: 16 parallel workers that enrich individual listings with detailed data

## 🏗️ Architecture Overview

The system uses a **parallel queue-based architecture** for high-performance data collection:

```
eBay Search Results → Collector Job → RabbitMQ Queue → 16x Worker Jobs → PostgreSQL Database
                                                                    ↓
                                                              FastAPI ← User Queries
```

**Key Benefits:**
- **16x Parallelization**: Concurrent listing enrichment for maximum throughput
- **Queue-based Processing**: Reliable work distribution with retry logic
- **Scalable Architecture**: Easy to scale workers or add new data sources
- **Production-ready**: Comprehensive monitoring, logging, and error handling

📊 **[View detailed architecture diagrams →](docs/architecture-diagram.md)**

## 🚀 Quick Start (Fresh WSL2 + MicroK8s)

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
- **RabbitMQ credentials**

📖 **[For manual setup, see the complete secrets guide](docs/SECRETS.md)**

### 3. Setup Python Environment (optional for local testing)
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

### 4. Deploy Complete System (Database + API + Scraper CronJob)
```bash
# Deploy everything (database + API + suspended scraper CronJob) with comprehensive testing
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

### Local Development (cluster-first)
```bash
# All components run in Kubernetes (MicroK8s)
# No local development needed - everything is containerized

# View logs and monitor the system
kubectl logs -f deployment/price-tracker-api -n price-tracker
kubectl logs -f deployment/postgres -n price-tracker

# Access the API directly
curl http://localhost:30080/health
```

### Testing
We provide offline unit tests for the scraper core logic and integration tests for deployed components.

```bash
# 1) Scraper offline unit tests (no network)
./tests/scraper_unit.sh

# 2) Integration tests to verify deployment
./database/test_integration.sh && ./api/test_api_integration.sh

# Or run everything with one command
chmod +x tests/run_all.sh && ./tests/run_all.sh
```
## 🕒 Parallel Scraper Architecture

The scraper now uses a **parallel queue-based architecture** for high-performance data collection:

### **Collector Job** (Search Results → Queue)
- Scrapes eBay search results pages
- Extracts listing metadata (title, price, URL)
- Queues listings for enrichment via RabbitMQ
- Runs as a Kubernetes Job (suspended CronJob by default)

### **Worker Jobs** (16 Parallel Enrichment Workers)
- 16 parallel workers process queued listings
- Each worker enriches individual listings with detailed data
- Handles bot detection, timeouts, and retry logic
- Saves enriched data to PostgreSQL

### **Queue Management**
- RabbitMQ handles message queuing and distribution
- Dead letter queue for failed messages
- Automatic retry with exponential backoff
- Message persistence and durability

### Running the Scraper
```bash
# Run collector job (scrapes search results and queues listings)
microk8s kubectl -n price-tracker create job --from=cronjob/ebay-collector ebay-collector-test-$(date +%s)

# Run worker jobs (16 parallel workers for enrichment)
microk8s kubectl -n price-tracker create job --from=cronjob/ebay-workers ebay-workers-test-$(date +%s)

# View collector logs
microk8s kubectl -n price-tracker logs -l job-name=ebay-collector-test-<timestamp> | cat

# View worker logs
microk8s kubectl -n price-tracker logs -l job-name=ebay-workers-test-<timestamp> | cat

# Check queue status
microk8s kubectl -n price-tracker exec deployment/rabbitmq -- rabbitmqctl list_queues
```

### Temporarily enable/disable scheduled runs:
```bash
# Enable scheduled runs
microk8s kubectl -n price-tracker patch cronjob ebay-collector -p '{"spec":{"suspend":false}}'
microk8s kubectl -n price-tracker patch cronjob ebay-workers -p '{"spec":{"suspend":false}}'

# Disable scheduled runs
microk8s kubectl -n price-tracker patch cronjob ebay-collector -p '{"spec":{"suspend":true}}'
microk8s kubectl -n price-tracker patch cronjob ebay-workers -p '{"spec":{"suspend":true}}'
```

### Persistent mounts (MicroK8s)
- For convenience in MicroK8s, the Jobs mount host paths under `/var/snap/microk8s/common/price-tracker`:
  - Debug snapshots: `/var/snap/microk8s/common/price-tracker/debug` (ENV `DEBUG_SNAPSHOT_DIR=/tmp/debug`)
  - Listing snapshots: `/var/snap/microk8s/common/price-tracker/snapshots` (ENV `SNAPSHOT_DIR=/tmp/snapshots`)
  - Browser profile: `/var/snap/microk8s/common/price-tracker/profile-ebay` (ENV `USER_DATA_DIR=/tmp/profile-ebay`)
  These paths are configured in `k8s/collector-job.yaml` and `k8s/worker-job.yaml` and persist across Jobs.

### Scraper configuration
- **Database**: Reads connection from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (wired from `postgres-secret`)
- **Queue**: RabbitMQ connection via `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`
- **Proxy**: Optional. If needed, create `scraper-proxy` with `http_proxy` and `https_proxy` keys
- **Search parameters**: Override by editing `k8s/collector-job.yaml` or `k8s/worker-job.yaml`
- **Worker parallelism**: Configured via `WORKER_PARALLELISM` (default: 16 workers)

### Browser Profile & Bot Detection Avoidance
- **Critical**: The scraper uses `USER_DATA_DIR=/tmp/profile-ebay` to maintain a persistent browser profile during scraping sessions
- **Why it matters**: eBay's bot detection is highly sensitive to fresh browser sessions without cookies/history
- **Profile benefits**:
  - Establishes consistent browser fingerprint and session data
  - Stores cookies and browsing history that make the scraper appear as a returning user
  - Significantly reduces bot detection triggers
  - Improves scraping success rate and listing discovery
- **Unlimited pages & enrichment**: `MAX_PAGES=0` scrapes all pages; `ENRICH_LIMIT=0` enriches all filtered listings
- **Human‑like navigation**: Click‑through from results (default), with goto fallback and URL verification
- **Challenge handling**: Wait/retry with reload (envs: `BLOCK_RECHECK`, `BLOCK_MAX_RETRIES`, `BLOCK_WAIT_MIN_S/MAX_S`)
- **Headless fingerprint**: Chromium `--headless=new` for a closer Chrome signature
- **Without proper profile**: Scraper may return 0 listings due to bot detection, even though the search logic is correct

### Incremental scraping behavior
- The scraper links listings to a `search_id` and performs incremental updates:
  - New `listing_id`s are upserted; previously seen ones are refreshed
  - Missing `listing_id`s from a run are marked inactive (`is_active=false`, `ended_at` timestamp)
  - Lifecycle fields on `price_tracker.listings`: `first_seen_at`, `last_seen_at`, `is_active`, `ended_at`
  - Toggle behavior via envs (optional):
    - `SEARCH_TERM` (default: "Selmer Mark VI")
    - `ENRICH_LIMIT` (number of detail pages to snapshot/enrich)

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
│   ├── collector-job.yaml # Collector job (search results → queue)
│   ├── worker-job.yaml    # Worker job (16 parallel enrichment workers)
│   ├── rabbitmq-deployment.yaml # RabbitMQ message queue
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
├── scraper/               # eBay Scraper (Playwright-based)
│   ├── config/           # Configuration management
│   │   └── settings.py   # Environment variable handling
│   ├── utils/            # Utility modules
│   │   ├── bot_detection.py  # Anti-bot detection & evasion
│   │   └── timeout_manager.py  # Timeout handling
│   ├── extractors/       # Data extraction modules
│   │   ├── results_parser.py   # Search results parsing
│   │   └── listing_enricher.py # Individual listing enrichment
│   ├── tests/            # Scraper unit tests
│   ├── playwright_ebay_scraper.py # Main scraper class
│   └── db.py            # Database operations
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

## 📖 Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Complete system architecture documentation
- **[Architecture Diagram](docs/architecture-diagram.md)** - Visual system architecture diagram
- **[Component Diagram](docs/component-diagram.md)** - Simplified component relationships
- **[Secrets Setup Guide](docs/SECRETS.md)** - Complete secrets configuration
- **[Monitoring Guide](docs/MONITORING.md)** - Grafana, Prometheus, and observability
- **[Integration Tests](tests/README.md)** - Testing documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## 📄 License

This project is licensed under the MIT License.
This repo was built as a learning experience with no commercial implications.

