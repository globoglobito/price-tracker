# Simple Integration Tests

This directory contains essential integration tests for the Price Tracker project.

## Quick Test

Run the simple test suite to verify your deployment is working:

```bash
# Make executable and run tests
chmod +x tests/run-tests.sh
./tests/run-tests.sh
```

## What the Tests Check

The test suite verifies the essential functionality:

### Environment Tests
- ✅ MicroK8s is running
- ✅ kubectl can connect to cluster

### Deployment Tests  
- ✅ Namespace exists
- ✅ PostgreSQL pod is running
- ✅ Application pod is running

### Database Tests
- ✅ Database is accessible
- ✅ Can connect to database

### Application Tests
- ✅ Application is healthy

## Expected Output

```
🚀 Starting Simple Integration Tests
=====================================

🧪 Test 1: MicroK8s is running
✅ PASSED: MicroK8s is running

🧪 Test 2: kubectl can connect
✅ PASSED: kubectl can connect

🧪 Test 3: Namespace exists
✅ PASSED: Namespace exists

🧪 Test 4: PostgreSQL pod is running
✅ PASSED: PostgreSQL pod is running

🧪 Test 5: Application pod is running
✅ PASSED: Application pod is running

🧪 Test 6: Database is accessible
✅ PASSED: Database is accessible

🧪 Test 7: Can connect to database
✅ PASSED: Can connect to database

🧪 Test 8: Application is healthy
✅ PASSED: Application is healthy

=====================================
📊 Test Results Summary
=====================================
Total tests run: 8
Tests passed: 8
Tests failed: 0

🎉 All essential tests passed! Your deployment is working.
```

## Troubleshooting

If tests fail:

1. **MicroK8s not running**: `microk8s start`
2. **Deployment not ready**: `./scripts/deploy.sh`
3. **Pods not running**: `kubectl get pods -n price-tracker`
4. **Database issues**: Check secrets and deployment logs

## Prerequisites

- MicroK8s installed and running
- Infrastructure deployed (`./scripts/deploy.sh`)
- kubectl configured for MicroK8s
