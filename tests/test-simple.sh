#!/bin/bash
# Simple Integration Tests for Price Tracker
# Essential tests for clone-and-go functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${BLUE}🧪 Test $TESTS_RUN: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo -e "${YELLOW}🚀 Starting Simple Integration Tests${NC}"
echo "====================================="
echo ""

# Essential environment tests
run_test "MicroK8s is running" "microk8s status --wait-ready --timeout 30 &>/dev/null"
run_test "kubectl can connect" "kubectl cluster-info &>/dev/null"

# Essential deployment tests
run_test "Namespace exists" "kubectl get namespace price-tracker &>/dev/null"
run_test "PostgreSQL pod is running" "kubectl get pod -l app=postgres -n price-tracker | grep -q Running"
run_test "Application pod is running" "kubectl get pod -l app=price-tracker -n price-tracker | grep -q Running"

# Essential database tests
run_test "Database is accessible" "kubectl exec -n price-tracker deployment/postgres -- pg_isready -U admin -d price_tracker_db &>/dev/null"
run_test "Can connect to database" "kubectl exec -n price-tracker deployment/postgres -- psql -U admin -d price_tracker_db -c 'SELECT 1;' &>/dev/null"

# Essential application tests
run_test "Application can connect to database" "kubectl logs -l app=price-tracker -n price-tracker | grep -q 'Database connection successful'"

echo ""
echo "====================================="
echo -e "${YELLOW}📊 Test Results Summary${NC}"
echo "====================================="
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All essential tests passed! Your deployment is working.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some tests failed. Check your deployment.${NC}"
    exit 1
fi 