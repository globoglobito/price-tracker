# Integration Tests

This directory contains comprehensive integration tests for the Price Tracker infrastructure setup.

## Test Suites

### 1. WSL2 Environment Tests (`test-wsl2.sh`)
- **Purpose**: Validates WSL2 environment and MicroK8s setup
- **Tests**: 25+ tests covering environment, networking, storage, and performance
- **When to run**: Before any deployment, especially on new WSL2 setups

### 2. CI/CD Pipeline Tests (`test-cicd.sh`)
- **Purpose**: Validates GitHub Actions workflow and Docker configurations  
- **Tests**: 20+ tests covering workflow files, security, and best practices
- **When to run**: After modifying CI/CD configurations or before deployment

### 3. Infrastructure Integration Tests (`test-infrastructure.sh`)
- **Purpose**: Validates complete Kubernetes deployment pipeline
- **Tests**: 15+ tests covering secrets, deployments, services, and connectivity
- **When to run**: After deployment to verify everything is working

### 4. Database Integration Tests (`test-database.sh`)
- **Purpose**: Validates PostgreSQL deployment and connectivity
- **Tests**: 15+ tests covering connectivity, security, performance, and WSL2 optimizations
- **When to run**: After database deployment to ensure it's ready for application

## Quick Start

### Run All Tests
```bash
# Make executable and run all tests
chmod +x tests/*.sh
./tests/run-tests.sh
```

### Run Specific Test Suites
```bash
# Test only WSL2 environment
./tests/run-tests.sh wsl2

# Test CI/CD configuration
./tests/run-tests.sh cicd

# Test infrastructure deployment
./tests/run-tests.sh infra database
```

### Run Tests Without Deployment
```bash
# Skip tests that require deployed resources
./tests/run-tests.sh --skip-deploy
```

## Test Categories

### 🌐 Environment Tests
- WSL2 configuration validation
- MicroK8s installation and status
- Storage and networking setup
- Performance optimization checks

### 🔐 Security Tests  
- Secrets management validation
- Non-root container execution
- Image pull secrets configuration
- No hardcoded credentials verification

### 🏗️ Infrastructure Tests
- Kubernetes resource deployment
- Service connectivity
- Persistent volume claims
- Label and selector consistency

### 🗄️ Database Tests
- PostgreSQL connectivity
- User permissions and privileges
- WSL2-specific optimizations
- Basic CRUD operations

### 🔄 CI/CD Tests
- GitHub Actions workflow validation
- Docker Hub integration
- Multi-architecture builds
- Security best practices

## Prerequisites

### Required Tools
- `kubectl` or `microk8s kubectl`
- `bash` (WSL2 environment)
- `curl` (for external connectivity tests)
- `nc` (netcat, for port testing)

### Optional Tools
- `yq` (for advanced YAML validation)
- `docker` CLI (for Docker Hub checks)
- `helm` (for Helm chart tests)

### Required Deployment
Some tests require the infrastructure to be deployed:
```bash
# Deploy infrastructure first
./scripts/deploy.sh

# Then run all tests
./tests/run-tests.sh
```

## Understanding Test Results

### ✅ Pass Criteria
- All resources are deployed and healthy
- Security configurations are correct
- Performance meets WSL2 requirements
- Network connectivity is functional

### ❌ Common Failures
- **WSL2 not configured**: Enable systemd, restart WSL2
- **MicroK8s not ready**: Check `microk8s status`, enable required addons
- **Secrets missing**: Run `kubectl apply -f k8s/secrets.yaml`
- **Database not ready**: Wait for PostgreSQL pod to be Running

## Test Output

### Results Location
- Console output: Real-time test results with color coding
- Results file: `/tmp/price_tracker_test_results.txt`

### Exit Codes
- `0`: All tests passed
- `1`: Some tests failed

### Color Coding
- 🔵 **Blue**: Test information and progress
- 🟢 **Green**: Test passed
- 🔴 **Red**: Test failed  
- 🟡 **Yellow**: Warnings or skipped tests

## Extending Tests

### Adding New Tests
1. Add test function to appropriate script
2. Use `run_test "Test Name" "test_command"` format
3. Update test counters and documentation

### Custom Test Suites
1. Create new test script in `tests/` directory
2. Follow existing script structure and naming
3. Add to `run-tests.sh` for integration

## Troubleshooting

### WSL2 Issues
```bash
# Check WSL2 version
wsl --status

# Enable systemd
echo '[boot]\nsystemd=true' | sudo tee -a /etc/wsl.conf
wsl --shutdown && wsl
```

### MicroK8s Issues  
```bash
# Check status
microk8s status --wait-ready

# Enable required addons
microk8s enable dns storage

# Reset if needed
microk8s reset
```

### Test Failures
```bash
# Run individual test for detailed output
./tests/test-infrastructure.sh

# Check specific resources
kubectl get all -n price-tracker
kubectl describe pod -l app=postgres -n price-tracker
```

## Integration with Development

### Pre-Commit Tests
```bash
# Quick validation before commits
./tests/run-tests.sh --quick wsl2 cicd
```

### Deployment Validation
```bash
# Full infrastructure validation
./scripts/deploy.sh
./tests/run-tests.sh infra database
```

### Continuous Integration
Tests are designed to be CI-friendly and can be integrated into GitHub Actions or other CI systems for automated validation.
