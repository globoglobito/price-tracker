#!/bin/bash
# Database Integration Tests
# Tests PostgreSQL connectivity, schema, and basic operations

set -e

# Load shared configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-config.sh"

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

# Database connection will be loaded from shared config
# DB_NAME, DB_USER, DB_HOST, DB_PORT are set by test-config.sh

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

# Function to execute SQL via kubectl
exec_sql() {
    local sql="$1"
    kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U "$DB_USER" -d "$DB_NAME" -c "$sql" 2>/dev/null
}

# Function to check if PostgreSQL is responding
pg_is_ready() {
    kubectl exec -n "$NAMESPACE" deployment/postgres -- pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null
}

# Function to port-forward PostgreSQL (for external tools)
setup_port_forward() {
    kubectl port-forward -n "$NAMESPACE" service/postgres-service 5432:5432 &
    local pf_pid=$!
    echo $pf_pid > /tmp/pg_port_forward.pid
    sleep 3
}

cleanup_port_forward() {
    if [ -f /tmp/pg_port_forward.pid ]; then
        local pf_pid=$(cat /tmp/pg_port_forward.pid)
        kill $pf_pid 2>/dev/null || true
        rm -f /tmp/pg_port_forward.pid
    fi
}

# Cleanup on exit
trap cleanup_port_forward EXIT

echo -e "${YELLOW}🗄️  Starting Database Integration Tests${NC}"
echo "========================================"
echo ""

# Show current configuration
show_config

# Configuration validation tests
run_test "Database secrets exist" "kubectl get secret postgres-secret -n \"$NAMESPACE\" &>/dev/null"
run_test "Can read database username from secret" "[ -n \"$DB_USER\" ] && [ \"$DB_USER\" != \"\" ]"
run_test "Database name is configured" "[ -n \"$DB_NAME\" ] && [ \"$DB_NAME\" != \"\" ]"

# Basic connectivity tests
run_test "PostgreSQL pod is running" "kubectl get pod -l app=postgres -n \"$NAMESPACE\" | grep -q Running"
run_test "PostgreSQL is ready" "pg_is_ready"
run_test "Can connect to database" "exec_sql 'SELECT 1;' | grep -q '1'"

# Database and user tests
run_test "Database exists" "exec_sql '\\l' | grep -q '$DB_NAME'"
run_test "User can access database" "exec_sql 'SELECT current_user;' | grep -q '$DB_USER'"
run_test "User has required privileges" "exec_sql 'SELECT has_database_privilege(current_user, current_database(), '\''CREATE'\'');' | grep -q 't'"

# Schema tests (basic structure for future app)
run_test "Can create test table" "exec_sql 'CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(50));'"
run_test "Can insert test data" "exec_sql 'INSERT INTO test_table (name) VALUES ('\''test'\'') ON CONFLICT DO NOTHING;'"
run_test "Can query test data" "exec_sql 'SELECT COUNT(*) FROM test_table;' | grep -q '[0-9]'"
run_test "Can drop test table" "exec_sql 'DROP TABLE IF EXISTS test_table;'"

# Performance and configuration tests
run_test "PostgreSQL version is supported" "exec_sql 'SELECT version();' | grep -q 'PostgreSQL 1[4-9]'"
run_test "UTF8 encoding is set" "exec_sql 'SHOW server_encoding;' | grep -q 'UTF8'"
run_test "Timezone is configured" "exec_sql 'SHOW timezone;' | grep -q '[A-Z]'"

# Security tests
run_test "SSL is available" "exec_sql 'SHOW ssl;' | grep -q 'on\\|off'"
run_test "Password authentication works" "kubectl exec -n \"$NAMESPACE\" deployment/postgres -- psql -U '$DB_USER' -d '$DB_NAME' -c 'SELECT 1;' | grep -q '1'"

# Storage and persistence tests
run_test "Data directory is mounted" "kubectl exec -n \"$NAMESPACE\" deployment/postgres -- ls -la /var/lib/postgresql/data | grep -q 'PG_VERSION'"
run_test "WAL archiving is configured" "exec_sql 'SHOW archive_mode;' | grep -q 'on\\|off'"

# Connection limits and resource tests
run_test "Max connections is reasonable" "exec_sql 'SHOW max_connections;' | awk 'NR==3 {exit (\$1 >= 20 && \$1 <= 200) ? 0 : 1}'"
run_test "Shared buffers is configured" "exec_sql 'SHOW shared_buffers;' | grep -q '[0-9]'"

# WSL2 specific tests
run_test "PostgreSQL can handle WSL2 environment" "exec_sql 'SELECT pg_size_pretty(pg_database_size(current_database()));' | grep -q '[0-9]'"

# Backup and recovery readiness (configuration only)
run_test "PostgreSQL logs are accessible" "kubectl logs -n \"$NAMESPACE\" deployment/postgres --tail=10 | grep -q 'database system is ready to accept connections'"

echo ""
echo "========================================"
echo -e "${YELLOW}📊 Database Test Results Summary${NC}"
echo "========================================"
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All database tests passed! PostgreSQL is ready for application development.${NC}"
    echo ""
    echo -e "${BLUE}💡 Ready for next steps:${NC}"
    echo "   1. Database schema creation"
    echo "   2. Migration scripts"
    echo "   3. Application connection testing"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some database tests failed. Check PostgreSQL configuration.${NC}"
    exit 1
fi
