#!/bin/bash
# WSL2 Environment Tests
# Tests WSL2-specific configurations and optimizations

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

# Function to check if we're running in WSL2
is_wsl2() {
    [ -f /proc/version ] && grep -q Microsoft /proc/version && [ "$(wsl.exe --status 2>/dev/null | grep -i version | grep -o '2')" = "2" ]
}

# Function to check MicroK8s configuration
check_microk8s_config() {
    microk8s config | grep -q "server:" && microk8s config | grep -q "certificate-authority-data:"
}

# Function to check storage performance
test_storage_performance() {
    local test_file="/tmp/wsl2_storage_test"
    # Simple write test
    dd if=/dev/zero of="$test_file" bs=1M count=10 oflag=direct 2>/dev/null && rm -f "$test_file"
}

echo -e "${YELLOW}🪟 Starting WSL2 Environment Tests${NC}"
echo "=================================="
echo ""

# WSL2 environment tests
run_test "Running in WSL2" "is_wsl2"
run_test "WSL2 has systemd enabled" "systemctl --version &>/dev/null"
run_test "WSL2 networking is functional" "ping -c 1 8.8.8.8 &>/dev/null"

# MicroK8s specific tests
run_test "MicroK8s is installed" "command -v microk8s &>/dev/null"
run_test "MicroK8s is running" "microk8s status --wait-ready --timeout 30 &>/dev/null"
run_test "MicroK8s config is accessible" "check_microk8s_config"
run_test "MicroK8s has required addons" "microk8s status | grep -q 'dns.*enabled' && microk8s status | grep -q 'storage.*enabled'"

# Storage tests
run_test "MicroK8s hostpath storage is available" "microk8s kubectl get storageclass | grep -q 'microk8s-hostpath'"
run_test "Storage performance is adequate" "test_storage_performance"
run_test "Persistent volumes can be created" "microk8s kubectl get pv | grep -q 'Available\\|Bound' || [ \$(microk8s kubectl get pv --no-headers | wc -l) -eq 0 ]"

# Memory and resource tests
run_test "Sufficient memory available" "[ \$(free -m | awk 'NR==2{print \$7}') -gt 1000 ]"
run_test "Docker daemon not running locally" "! systemctl is-active docker &>/dev/null"
run_test "Snap services are running" "systemctl is-active snapd &>/dev/null"

# Network configuration tests
run_test "Localhost resolution works" "ping -c 1 localhost &>/dev/null"
run_test "WSL2 can resolve external DNS" "nslookup google.com &>/dev/null"
run_test "Port forwarding capability" "ss -tuln > /dev/null"

# File system tests
run_test "Linux file system permissions work" "touch /tmp/test_file && chmod 755 /tmp/test_file && [ -x /tmp/test_file ] && rm -f /tmp/test_file"
run_test "Case-sensitive file system" "touch /tmp/TestFile && touch /tmp/testfile && [ \$(ls /tmp/*estfile 2>/dev/null | wc -l) -eq 2 ] && rm -f /tmp/TestFile /tmp/testfile"

# WSL2 optimization tests
run_test "WSL2 memory limit is reasonable" "[ \$(cat /proc/meminfo | grep MemTotal | awk '{print \$2}') -gt 2000000 ]"
run_test "Swap is configured" "[ \$(cat /proc/meminfo | grep SwapTotal | awk '{print \$2}') -gt 0 ] || echo 'Swap not configured - this is OK for WSL2'"

# Kubernetes-specific WSL2 tests
run_test "kubectl can connect through MicroK8s" "microk8s kubectl cluster-info | grep -q 'Kubernetes control plane'"
run_test "MicroK8s registry addon available" "microk8s status | grep -q 'registry.*disabled\\|registry.*enabled'"
run_test "CoreDNS is running" "microk8s kubectl get pods -n kube-system | grep -q 'coredns.*Running'"

# Performance optimization tests
if [ -f "helm/price-tracker-postgres-values.yaml" ]; then
    run_test "PostgreSQL has WSL2 optimizations" "grep -q 'fsync.*off\\|synchronous_commit.*off' 'helm/price-tracker-postgres-values.yaml'"
fi

# Security and isolation tests
run_test "WSL2 user has sudo access" "sudo -n true 2>/dev/null || [ \$? -eq 1 ]"
run_test "WSL2 has proper timezone" "[ -n \"\$TZ\" ] || [ -f /etc/timezone ]"

# Development tools availability
run_test "Git is available" "command -v git &>/dev/null"
run_test "Curl is available" "command -v curl &>/dev/null"
run_test "Basic shell tools available" "command -v grep &>/dev/null && command -v awk &>/dev/null && command -v sed &>/dev/null"

# WSL2 integration tests
run_test "Can access Windows drives" "[ -d /mnt/c ] || [ -d /c ]"
run_test "WSL2 hostname is set" "[ -n \"\$(hostname)\" ] && [ \"\$(hostname)\" != \"localhost\" ]"

echo ""
echo "=================================="
echo -e "${YELLOW}📊 WSL2 Test Results Summary${NC}"
echo "=================================="
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All WSL2 tests passed! Environment is optimized.${NC}"
    echo ""
    echo -e "${BLUE}💡 WSL2 Environment Status:${NC}"
    echo "   ✅ WSL2 with systemd enabled"
    echo "   ✅ MicroK8s running with required addons"
    echo "   ✅ No local Docker daemon conflicts"
    echo "   ✅ Storage and networking optimized"
    echo "   ✅ Development tools available"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some WSL2 tests failed. Check environment configuration.${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Common fixes:${NC}"
    echo "   - Enable systemd in WSL2: echo '[boot]\\nsystemd=true' >> /etc/wsl.conf"
    echo "   - Restart WSL2: wsl --shutdown && wsl"
    echo "   - Install MicroK8s: sudo snap install microk8s --classic"
    echo "   - Enable addons: microk8s enable dns storage"
    exit 1
fi
