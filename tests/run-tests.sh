#!/bin/bash
# Master Test Runner for Price Tracker
# Runs all integration tests in the correct order

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Test suite configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS_FILE="/tmp/price_tracker_test_results.txt"

# Initialize results file
echo "Price Tracker Integration Test Results - $(date)" > "$TEST_RESULTS_FILE"
echo "=============================================" >> "$TEST_RESULTS_FILE"

# Function to run a test suite
run_test_suite() {
    local suite_name="$1"
    local script_name="$2"
    local script_path="$SCRIPT_DIR/$script_name"
    
    echo ""
    echo -e "${PURPLE}🚀 Running $suite_name${NC}"
    echo "=================================="
    
    if [ ! -f "$script_path" ]; then
        echo -e "${RED}❌ Test script not found: $script_path${NC}"
        echo "FAILED: $suite_name - Script not found" >> "$TEST_RESULTS_FILE"
        return 1
    fi
    
    if [ ! -x "$script_path" ]; then
        echo -e "${YELLOW}⚠️  Making test script executable: $script_name${NC}"
        chmod +x "$script_path"
    fi
    
    echo "Started: $(date)" >> "$TEST_RESULTS_FILE"
    echo "Suite: $suite_name" >> "$TEST_RESULTS_FILE"
    
    if "$script_path"; then
        echo -e "${GREEN}✅ $suite_name - ALL TESTS PASSED${NC}"
        echo "PASSED: $suite_name" >> "$TEST_RESULTS_FILE"
        return 0
    else
        echo -e "${RED}❌ $suite_name - SOME TESTS FAILED${NC}"
        echo "FAILED: $suite_name" >> "$TEST_RESULTS_FILE"
        return 1
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}Price Tracker Integration Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_SUITES...]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -q, --quick    Run quick tests only (skip lengthy tests)"
    echo "  -v, --verbose  Verbose output"
    echo "  --skip-deploy  Skip tests that require deployed resources"
    echo ""
    echo "Test Suites:"
    echo "  wsl2       - WSL2 environment and MicroK8s tests"
    echo "  cicd       - CI/CD pipeline and configuration tests"
    echo "  infra      - Infrastructure and Kubernetes deployment tests"
    echo "  database   - Database connectivity and functionality tests"
    echo "  all        - Run all test suites (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 wsl2 cicd         # Run only WSL2 and CI/CD tests"
    echo "  $0 --quick           # Run quick tests only"
    echo "  $0 --skip-deploy all # Run all tests except those requiring deployment"
}

# Parse command line arguments
QUICK_MODE=false
VERBOSE=false
SKIP_DEPLOY=false
TEST_SUITES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        wsl2|cicd|infra|database|all)
            TEST_SUITES+=("$1")
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Default to all tests if none specified
if [ ${#TEST_SUITES[@]} -eq 0 ]; then
    TEST_SUITES=("all")
fi

# If "all" is specified, expand to all test suites
if [[ " ${TEST_SUITES[@]} " =~ " all " ]]; then
    if [ "$SKIP_DEPLOY" = true ]; then
        TEST_SUITES=("wsl2" "cicd")
    else
        TEST_SUITES=("wsl2" "cicd" "infra" "database")
    fi
fi

echo -e "${PURPLE}🧪 Price Tracker Integration Test Runner${NC}"
echo "========================================"
echo -e "📅 Date: ${BLUE}$(date)${NC}"
echo -e "🖥️  Environment: ${BLUE}WSL2 + MicroK8s${NC}"
echo -e "📊 Test Suites: ${BLUE}${TEST_SUITES[*]}${NC}"
echo -e "⚡ Quick Mode: ${BLUE}$QUICK_MODE${NC}"
echo -e "🚀 Skip Deploy: ${BLUE}$SKIP_DEPLOY${NC}"

# Track overall results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Run test suites in optimal order
for suite in "${TEST_SUITES[@]}"; do
    case $suite in
        wsl2)
            TOTAL_SUITES=$((TOTAL_SUITES + 1))
            if run_test_suite "WSL2 Environment Tests" "test-wsl2.sh"; then
                PASSED_SUITES=$((PASSED_SUITES + 1))
            else
                FAILED_SUITES=$((FAILED_SUITES + 1))
                if [ "$suite" = "wsl2" ]; then
                    echo -e "${YELLOW}⚠️  WSL2 tests failed - some subsequent tests may fail${NC}"
                fi
            fi
            ;;
        cicd)
            TOTAL_SUITES=$((TOTAL_SUITES + 1))
            if run_test_suite "CI/CD Pipeline Tests" "test-cicd.sh"; then
                PASSED_SUITES=$((PASSED_SUITES + 1))
            else
                FAILED_SUITES=$((FAILED_SUITES + 1))
            fi
            ;;
        infra)
            if [ "$SKIP_DEPLOY" = false ]; then
                TOTAL_SUITES=$((TOTAL_SUITES + 1))
                if run_test_suite "Infrastructure Integration Tests" "test-infrastructure.sh"; then
                    PASSED_SUITES=$((PASSED_SUITES + 1))
                else
                    FAILED_SUITES=$((FAILED_SUITES + 1))
                    echo -e "${YELLOW}⚠️  Infrastructure tests failed - database tests may fail${NC}"
                fi
            else
                echo -e "${YELLOW}⏭️  Skipping infrastructure tests (--skip-deploy)${NC}"
            fi
            ;;
        database)
            if [ "$SKIP_DEPLOY" = false ]; then
                TOTAL_SUITES=$((TOTAL_SUITES + 1))
                if run_test_suite "Database Integration Tests" "test-database.sh"; then
                    PASSED_SUITES=$((PASSED_SUITES + 1))
                else
                    FAILED_SUITES=$((FAILED_SUITES + 1))
                fi
            else
                echo -e "${YELLOW}⏭️  Skipping database tests (--skip-deploy)${NC}"
            fi
            ;;
    esac
done

# Final results
echo ""
echo "============================================="
echo -e "${PURPLE}📊 Final Test Results Summary${NC}"
echo "============================================="
echo -e "Total test suites run: ${BLUE}$TOTAL_SUITES${NC}"
echo -e "Test suites passed: ${GREEN}$PASSED_SUITES${NC}"
echo -e "Test suites failed: ${RED}$FAILED_SUITES${NC}"

# Add to results file
echo "" >> "$TEST_RESULTS_FILE"
echo "FINAL SUMMARY:" >> "$TEST_RESULTS_FILE"
echo "Total: $TOTAL_SUITES, Passed: $PASSED_SUITES, Failed: $FAILED_SUITES" >> "$TEST_RESULTS_FILE"
echo "Finished: $(date)" >> "$TEST_RESULTS_FILE"

if [ $FAILED_SUITES -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TEST SUITES PASSED! 🎉${NC}"
    echo -e "${GREEN}Infrastructure is ready for application development!${NC}"
    echo ""
    echo -e "${BLUE}💡 Next Steps:${NC}"
    echo "   1. Start building your Price Tracker application"
    echo "   2. Add application-specific unit tests"
    echo "   3. Create end-to-end user tests"
    echo "   4. Set up monitoring and observability"
    echo ""
    echo -e "${BLUE}📄 Full test results: ${TEST_RESULTS_FILE}${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 SOME TEST SUITES FAILED${NC}"
    echo -e "${RED}Please fix the failing tests before proceeding${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "   1. Check individual test output above"
    echo "   2. Verify WSL2 and MicroK8s setup"
    echo "   3. Ensure all secrets are created"
    echo "   4. Run individual test suites for detailed output"
    echo ""
    echo -e "${BLUE}📄 Full test results: ${TEST_RESULTS_FILE}${NC}"
    exit 1
fi
