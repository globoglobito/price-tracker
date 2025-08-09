# Integration Tests

This directory contains comprehensive integration tests for the Price Tracker project.

## Test Suites

We have two comprehensive test suites that can be run independently:

### Database Integration Tests
Tests the PostgreSQL database schema and functionality:

```bash
# Run database tests
./database/test_integration.sh
```

**What it tests (20 tests):**
- ✅ Database connectivity
- ✅ Schema creation and isolation (`price_tracker` schema)
- ✅ Table structure and constraints (`searches`, `listings`)
- ✅ Index creation and usage
- ✅ Data insertion (rich and minimal data)
- ✅ Data retrieval and querying
- ✅ Data type validation
- ✅ Cleanup operations

### API Integration Tests
Tests the FastAPI Search API functionality:

```bash
# Run API tests
./api/test_api_integration.sh
```

**What it tests (15 tests):**
- ✅ API pod is running
- ✅ Health and documentation endpoints
- ✅ Search CRUD operations (Create, Read, Update, Delete)
- ✅ Search status toggling
- ✅ Error handling
- ✅ JSON response structure

## Quick Test

Run both test suites to verify your complete deployment:

```bash
# Run all tests
./database/test_integration.sh && ./api/test_api_integration.sh
```

## Expected Output

### Database Tests
```
🔍 Starting Database Integration Tests
=============================================

🧪 Test 1: Database connection
✅ PASSED: Database connection

🧪 Test 2: Price tracker schema exists
✅ PASSED: Price tracker schema exists

... (18 more tests)

=============================================
📊 Integration Test Results Summary
=============================================
Total tests run: 20
Tests passed: 20
Tests failed: 0

🎉 All integration tests passed! Database schema is working correctly.
```

### API Tests
```
🔍 Starting API Integration Tests
=============================================

🧪 Test 1: API pod is running
✅ PASSED: API pod is running

🧪 Test 2: API health endpoint responds
✅ PASSED: API health endpoint responds

... (13 more tests)

=============================================
📊 API Integration Test Results Summary
=============================================
Total tests run: 15
Tests passed: 15
Tests failed: 0

🎉 All API integration tests passed! Search API is working correctly.
```

## Troubleshooting

If tests fail:

1. **Database tests failing**: 
   - Check PostgreSQL pod: `kubectl get pods -n price-tracker -l app=postgres`
   - Check database logs: `kubectl logs -f deployment/postgres -n price-tracker`

2. **API tests failing**:
   - Check API pod: `kubectl get pods -n price-tracker -l app=price-tracker-api`
   - Check API logs: `kubectl logs -f deployment/price-tracker-api -n price-tracker`

3. **Deployment not ready**: 
   - Run complete deployment: `./scripts/deploy-complete.sh`

4. **MicroK8s issues**: 
   - Start MicroK8s: `microk8s start`
   - Check kubectl: `microk8s kubectl get nodes`

## Prerequisites

- MicroK8s installed and running
- Infrastructure deployed (`./scripts/deploy-complete.sh`)
- kubectl configured for MicroK8s (`sudo snap alias microk8s.kubectl kubectl`)

## Test Independence

Each test suite can be run independently:

```bash
# Test just the database
./database/test_integration.sh

# Test just the API
./api/test_api_integration.sh

# Test everything
./database/test_integration.sh && ./api/test_api_integration.sh
```

This allows you to focus on testing specific components during development.
