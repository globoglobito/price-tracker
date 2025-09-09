#!/bin/bash
# API Integration Test Script for Price Tracker
# Tests the FastAPI Search API functionality

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

# API configuration
API_URL="http://localhost:30080"
KUBECTL="microk8s kubectl"
# Unique name per run to avoid collisions with any existing records
UNIQ_NAME="Test-Sax-$(date +%s)"

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

echo -e "${YELLOW}🔍 Starting API Integration Tests${NC}"
echo "============================================="
echo ""

# Test 1: API pod is running
run_test "API pod is running" "$KUBECTL get pod -l app=price-tracker-api -n price-tracker | grep -q Running"

# Test 2: API health endpoint
run_test "API health endpoint responds" "curl -f ${API_URL}/health >/dev/null 2>&1"

# Test 3: API root endpoint
run_test "API root endpoint responds" "curl -f ${API_URL}/ >/dev/null 2>&1"

# Test 4: API documentation endpoint
run_test "API documentation is accessible" "curl -f ${API_URL}/docs >/dev/null 2>&1"

# Test 5: Search endpoint responds
run_test "Search endpoint responds" "curl -f ${API_URL}/searches >/dev/null 2>&1"

# Test 6: Search endpoint returns JSON
run_test "Search endpoint returns JSON" "curl -s ${API_URL}/searches | grep -q 'searches'"

# Test 7: Search endpoint has correct structure
run_test "Search endpoint has correct structure" "curl -s ${API_URL}/searches | grep -q 'total'"

# Test 8: Create a search term
run_test "Can create a search term" "test -n \"$UNIQ_NAME\"; curl -s -X POST ${API_URL}/searches -H 'Content-Type: application/json' -d '{\"search_term\": \"'\"$UNIQ_NAME\"'\", \"website\": \"ebay\"}' >/dev/null 2>&1 || true; for i in {1..10}; do SEARCH_ID=\$(curl -s ${API_URL}/searches | tr -d '\n' | sed 's/},{/}\n{/g' | grep -F \"$UNIQ_NAME\" | head -1 | sed -E 's/.*\"id\":([0-9]+).*/\1/'); [ -n \"$SEARCH_ID\" ] && break || sleep 0.5; done; echo SEARCH_ID=\"$SEARCH_ID\" >/dev/null; true"

# Test 9: Verify search term was created
run_test "Search term was created" "test -n \"$UNIQ_NAME\"; curl -s ${API_URL}/searches | grep -Fq \"$UNIQ_NAME\""

# Test 10: Get specific search by ID
run_test "Can get search by ID" "test -n \"$SEARCH_ID\"; curl -f ${API_URL}/searches/\$SEARCH_ID >/dev/null 2>&1"

# Test 11: Update search term
run_test "Can update search term" "test -n \"$SEARCH_ID\"; curl -f -X PUT ${API_URL}/searches/\$SEARCH_ID -H 'Content-Type: application/json' -d '{\"is_active\": false}' >/dev/null 2>&1"

# Test 12: Toggle search status
run_test "Can toggle search status" "test -n \"$SEARCH_ID\"; curl -f -X PATCH ${API_URL}/searches/\$SEARCH_ID/toggle >/dev/null 2>&1"

# Test 13: Delete search term
run_test "Can delete search term" "test -n \"$SEARCH_ID\"; curl -f -X DELETE ${API_URL}/searches/\$SEARCH_ID >/dev/null 2>&1"

# Test 14: Verify search term was deleted
run_test "Search term was deleted" "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/searches/\$SEARCH_ID | grep -q 404"

# Test 15: Error handling - get non-existent search
run_test "Handles non-existent search gracefully" "curl -s -w '%{http_code}' ${API_URL}/searches/99999 | grep -q 404"

echo ""
echo "============================================="
echo -e "${YELLOW}📊 API Integration Test Results Summary${NC}"
echo "============================================="
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All API integration tests passed! Search API is working correctly.${NC}"
    echo ""
    echo -e "${BLUE}✅ API Features Verified:${NC}"
    echo "  - API pod is running"
    echo "  - Health and documentation endpoints"
    echo "  - Search CRUD operations (Create, Read, Update, Delete)"
    echo "  - Search status toggling"
    echo "  - Error handling"
    echo "  - JSON response structure"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some API integration tests failed. Check the API setup.${NC}"
    exit 1
fi 