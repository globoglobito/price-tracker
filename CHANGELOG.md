# Changelog

All notable changes to this project will be documented here.

## [v0.1.0] - 2025-08-04

### ✨ Features
- **Initial Project Structure**: Basic folder structure and configuration files
- **Kubernetes Secrets Management**: Complete secrets integration for PostgreSQL, Docker Hub, and application credentials
- **WSL2 Optimization**: Performance-tuned configurations for WSL2 + MicroK8s environment
- **Multi-Deployment Options**: Support for both Helm and pure Kubernetes deployments
- **Enhanced CI/CD**: Multi-architecture Docker builds with GitHub Actions caching

### 🔐 Security
- **Removed Hardcoded Passwords**: All credentials now use Kubernetes secrets
- **Container Security**: Non-root containers with minimal privileges and security contexts
- **Image Pull Secrets**: Secure Docker Hub authentication for private repositories

### 🛠️ Infrastructure
- **PostgreSQL Helm Integration**: Bitnami PostgreSQL chart with secrets-based configuration
- **Storage Optimization**: WSL2-optimized persistent volumes with proper permissions
- **Network Security**: ClusterIP services with DNS-based service discovery

### 📖 Documentation
- **Complete Setup Guide**: Comprehensive WSL2 + MicroK8s setup without local Docker
- **Secrets Reference**: Detailed documentation of all required secrets (4 K8s + 2 GitHub)
- **Troubleshooting Guide**: WSL2-specific troubleshooting and optimization tips
- **Deployment Scripts**: Automated deployment with environment validation

### 🧹 Maintenance
- **Removed PowerShell Dependencies**: Streamlined to bash-only scripts for WSL2 focus
- **Enhanced Error Handling**: Better retry logic and validation in deployment scripts
- **Improved File Structure**: Organized configurations with clear separation of concerns

### 💥 Breaking Changes
- **Secrets Required**: All deployments now require proper Kubernetes secrets setup
- **Environment Variables**: Database credentials moved from ConfigMaps to Secrets
- **Deployment Process**: Manual Docker registry secret creation required before deployment

### 🔧 Technical Details
- Added 4 Kubernetes secrets: `postgres-secret`, `price-tracker-postgres-credentials`, `docker-registry-secret`, `app-secrets`
- Enhanced GitHub Actions with multi-arch builds (amd64, arm64)
- Optimized PostgreSQL configuration for WSL2 resource constraints
- Implemented proper health checks and resource limits for all containers
- Docker images: `globoglobitos/price-tracker:latest`, `globoglobitos/price-tracker:0.1.0`

