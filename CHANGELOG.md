# Changelog

All notable changes to this project will be documented here.

## [v0.3.0] - 2025-01-09

### 🚀 **Parallel Architecture Implementation**
- **Queue-Based Processing**: Implemented RabbitMQ message queue for distributed scraping
- **Collector/Worker Separation**: Split scraper into two distinct components:
  - **Collector Job**: Scrapes eBay search results and queues listings for enrichment
  - **Worker Jobs**: 16 parallel workers that enrich individual listings with detailed data
- **High-Performance Processing**: 16x parallelization for listing enrichment
- **Message Queue Integration**: RabbitMQ handles queuing, distribution, and retry logic
- **Dead Letter Queue**: Failed messages are routed to DLQ for analysis and retry

### 🔧 **Infrastructure Improvements**
- **RabbitMQ Deployment**: Added RabbitMQ message broker to Kubernetes cluster
- **Worker Parallelism**: Configurable worker count (default: 16 workers)
- **Queue Management**: Comprehensive queue monitoring and statistics
- **Message Persistence**: Durable message storage with TTL and retry policies
- **Resource Optimization**: Better resource utilization across multiple workers

### 🧪 **Testing Enhancements**
- **Comprehensive Test Suite**: Added 21 new unit tests for collector, worker, and queue manager
- **Test Coverage**: 43 total tests covering all major components
- **Mock Infrastructure**: Robust mocking for Playwright, RabbitMQ, and database operations
- **Integration Testing**: End-to-end testing of parallel architecture flow

### 📚 **Documentation Updates**
- **Architecture Documentation**: Updated README with parallel architecture details
- **Deployment Guides**: Updated deployment instructions for collector/worker jobs
- **Queue Management**: Added RabbitMQ configuration and monitoring documentation
- **Performance Metrics**: Documented 16-worker parallel processing capabilities

## [v0.2.0] - 2025-01-08

### 🔧 **Major Refactoring**
- **Scraper Architecture Redesign**: Completely refactored the eBay scraper from a single 1110-line file into a modular, maintainable architecture
- **Code Organization**: Split scraper into focused modules:
  - `config/settings.py` - Environment variable handling (150 lines)
  - `utils/bot_detection.py` - Anti-bot detection utilities (80 lines)  
  - `utils/timeout_manager.py` - Timeout management with 4-minute extraction timeout (100 lines)
  - `extractors/results_parser.py` - Search results parsing (150 lines)
  - `extractors/listing_enricher.py` - Individual listing enrichment (350 lines)
- **Improved Maintainability**: 59% reduction in main file size (1110 → 454 lines)
- **Enhanced Testability**: Each component can now be unit tested independently
- **Better Separation of Concerns**: Clear boundaries between configuration, utilities, and data extraction

### 🐛 **Bug Fixes**
- **Fixed Extraction Timeout Issue**: Added comprehensive timeout protection to prevent scraper hanging during data extraction
- **Improved Error Handling**: Better timeout detection and graceful fallback for problematic listings
- **Test Infrastructure**: Fixed broken imports and added comprehensive test coverage for new modules

### ✅ **Backward Compatibility**
- **Production Entry Point**: `python -m scraper.playwright_ebay_scraper` continues to work unchanged
- **API Compatibility**: All external interfaces remain the same
- **Configuration**: All environment variables work exactly as before
- **Docker/K8s**: No changes needed for containerized deployments

### 📚 **Documentation**
- **Updated Project Structure**: README now reflects the new modular architecture
- **Test Coverage**: Added unit tests for configuration, results parsing, and utility functions
- **Code Documentation**: Enhanced docstrings and module-level documentation

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

