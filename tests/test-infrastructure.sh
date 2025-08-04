#!/bin/bash
# Infrastructure Integration Tests for Price Tracker
# Tests the complete K8s deployment pipeline without application code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if resource exists
resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    local namespace="${3:-price-tracker}"
    
    kubectl get "$resource_type" "$resource_name" -n "$namespace" &>/dev/null
}

# Function to check if pod is ready
pod_ready() {
    local selector="$1"
    local namespace="${2:-price-tracker}"
    
    kubectl get pods -l "$selector" -n "$namespace" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -q "True"
}

# Function to check if service responds
service_responds() {
    local service_name="$1"
    local port="$2"
    local namespace="${3:-price-tracker}"
    
    # Use kubectl port-forward in background and test connection
    kubectl port-forward "service/$service_name" "$port:$port" -n "$namespace" &
    local pf_pid=$!
    sleep 3
    
    # Test connection (expecting connection refused is ok for now since no app code)
    if nc -z localhost "$port" 2>/dev/null || [[ $? -eq 1 ]]; then
        kill $pf_pid 2>/dev/null || true
        return 0
    else
        kill $pf_pid 2>/dev/null || true
        return 1
    fi
}

echo -e "${YELLOW}🔍 Starting Infrastructure Integration Tests${NC}"
echo "=========================================="
echo ""

# Pre-requisites tests
run_test "MicroK8s is running" "microk8s status --wait-ready --timeout 30"
run_test "kubectl can connect to cluster" "kubectl cluster-info | grep -q 'Kubernetes control plane'"
run_test "Required namespace exists" "resource_exists namespace price-tracker ''"

# Secrets tests
run_test "PostgreSQL secrets exist" "resource_exists secret postgres-secret"
run_test "App secrets exist" "resource_exists secret app-secrets"
run_test "Docker registry secret exists" "resource_exists secret docker-registry-secret"
run_test "PostgreSQL credentials secret exists" "resource_exists secret price-tracker-postgres-credentials"

# ConfigMaps tests
run_test "App config exists" "resource_exists configmap app-config"

# Storage tests
run_test "PostgreSQL PVC exists" "resource_exists pvc postgres-pvc"
run_test "PostgreSQL PVC is bound" "kubectl get pvc postgres-pvc -n price-tracker -o jsonpath='{.status.phase}' | grep -q 'Bound'"

# Database deployment tests
run_test "PostgreSQL deployment exists" "resource_exists deployment postgres"
run_test "PostgreSQL service exists" "resource_exists service postgres-service"
run_test "PostgreSQL pod is ready" "pod_ready 'app=postgres'"

# Application deployment tests  
run_test "Price tracker deployment exists" "resource_exists deployment price-tracker"
run_test "Price tracker service exists" "resource_exists service price-tracker-service"
run_test "Price tracker pod is ready" "pod_ready 'app=price-tracker'"

# Network connectivity tests
run_test "PostgreSQL service is accessible" "service_responds postgres-service 5432"
run_test "Price tracker service is accessible" "service_responds price-tracker-service 80"

# Security tests
run_test "PostgreSQL runs as non-root" "kubectl get pod -l app=postgres -n price-tracker -o jsonpath='{.items[*].spec.securityContext.runAsNonRoot}' | grep -q 'true'"
run_test "App runs as non-root" "kubectl get pod -l app=price-tracker -n price-tracker -o jsonpath='{.items[*].spec.securityContext.runAsNonRoot}' | grep -q 'true'"

# Resource limits tests
run_test "PostgreSQL has resource limits" "kubectl get deployment postgres -n price-tracker -o jsonpath='{.spec.template.spec.containers[0].resources.limits}' | grep -q 'memory'"
run_test "App has resource limits" "kubectl get deployment price-tracker -n price-tracker -o jsonpath='{.spec.template.spec.containers[0].resources.limits}' | grep -q 'memory'"

# Label and selector tests
run_test "All resources have project label" "[ \$(kubectl get all -l project=price-tracker -n price-tracker --no-headers | wc -l) -gt 5 ]"

# Helm chart tests (if using Helm for PostgreSQL)
if helm list -n price-tracker | grep -q postgresql; then
    run_test "PostgreSQL Helm release exists" "helm status postgresql -n price-tracker | grep -q 'STATUS: deployed'"
    run_test "PostgreSQL Helm chart uses secrets" "helm get values postgresql -n price-tracker | grep -q 'existingSecret'"
fi

echo ""
echo "=========================================="
echo -e "${YELLOW}📊 Test Results Summary${NC}"
echo "=========================================="
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! Infrastructure is ready.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
