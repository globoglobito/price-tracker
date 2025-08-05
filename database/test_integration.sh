#!/bin/bash
# Database Integration Test Script for Price Tracker
# Tests the complete database migration and schema functionality

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

# Use microk8s kubectl for all operations
KUBECTL="microk8s kubectl"

# Database connection parameters
DB_USER=${DB_USER:-"admin"}
DB_NAME=${DB_NAME:-"price_tracker_db"}

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

echo -e "${YELLOW}🔍 Starting Database Integration Tests${NC}"
echo "============================================="
echo ""

# Test 1: Database connectivity
run_test "Database connection" "$KUBECTL exec -n price-tracker deployment/postgres -- pg_isready -U $DB_USER -d $DB_NAME >/dev/null 2>&1"

# Test 2: Schema exists
run_test "Price tracker schema exists" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'price_tracker';\" | grep -q price_tracker"

# Test 3: Tables exist
run_test "Searches table exists" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT table_name FROM information_schema.tables WHERE table_schema = 'price_tracker' AND table_name = 'searches';\" | grep -q searches"

run_test "Listings table exists" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT table_name FROM information_schema.tables WHERE table_schema = 'price_tracker' AND table_name = 'listings';\" | grep -q listings"

# Test 4: Required columns exist
run_test "Searches table has required columns" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'price_tracker' AND table_name = 'searches' AND column_name IN ('id', 'search_term', 'website', 'is_active');\" | grep -q '4'"

run_test "Listings table has required columns" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'price_tracker' AND table_name = 'listings' AND column_name IN ('id', 'listing_name', 'price', 'url', 'website', 'scraped_at');\" | grep -q '6'"

# Test 5: Indexes exist
run_test "Listings indexes exist" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'price_tracker' AND tablename = 'listings' AND indexname LIKE 'idx_listings_%';\" | grep -q '5'"

run_test "Searches indexes exist" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'price_tracker' AND tablename = 'searches' AND indexname LIKE 'idx_searches_%';\" | grep -q '2'"

# Test 6: Constraints exist
run_test "Primary key constraints exist" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'price_tracker' AND constraint_type = 'PRIMARY KEY';\" | grep -q '2'"

run_test "Unique constraint on searches" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT constraint_name FROM information_schema.table_constraints WHERE table_schema = 'price_tracker' AND table_name = 'searches' AND constraint_type = 'UNIQUE';\" | grep -q 'searches_search_term_website_key'"

# Test 7: Data insertion (searches)
run_test "Can insert into searches table" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -c \"SET search_path TO price_tracker, public; INSERT INTO searches (search_term, website) VALUES ('Test Search', 'test-site') ON CONFLICT DO NOTHING;\" >/dev/null 2>&1"

# Test 8: Data insertion (listings - rich data)
run_test "Can insert rich data into listings" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -c \"SET search_path TO price_tracker, public; INSERT INTO listings (listing_name, price, url, website, scraped_at, brand, model, type, location) VALUES ('Test Rich Listing', 1500.00, 'https://test.com/item1', 'test-site', NOW(), 'TestBrand', 'TestModel', 'Tenor', 'Test Location');\" >/dev/null 2>&1"

# Test 9: Data insertion (listings - minimal data)
run_test "Can insert minimal data into listings" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -c \"SET search_path TO price_tracker, public; INSERT INTO listings (listing_name, price, url, website, scraped_at) VALUES ('Test Minimal Listing', 500.00, 'https://test.com/item2', 'test-site', NOW());\" >/dev/null 2>&1"

# Test 10: Data retrieval
run_test "Can query searches table" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SET search_path TO price_tracker, public; SELECT COUNT(*) FROM searches WHERE search_term = 'Test Search';\" | grep -q '1'"

run_test "Can query listings table" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SET search_path TO price_tracker, public; SELECT COUNT(*) FROM listings WHERE website = 'test-site';\" | grep -q '2'"

# Test 11: Index usage verification
run_test "Indexes are being used" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SET search_path TO price_tracker, public; EXPLAIN (FORMAT JSON) SELECT * FROM listings WHERE website = 'test-site';\" | grep -q 'Index Scan'"

# Test 12: Schema isolation
run_test "Schema isolation works" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('searches', 'listings');\" | grep -q '0'"

# Test 13: Data types validation
run_test "Price column accepts decimal values" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -c \"SET search_path TO price_tracker, public; INSERT INTO listings (listing_name, price, url, website, scraped_at) VALUES ('Decimal Test', 1234.56, 'https://test.com/decimal', 'test-site', NOW());\" >/dev/null 2>&1"

run_test "Timestamp columns work correctly" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c \"SET search_path TO price_tracker, public; SELECT COUNT(*) FROM listings WHERE scraped_at IS NOT NULL;\" | grep -q '[1-9]'"

# Test 14: Cleanup test data
run_test "Can delete test data" "$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -c \"SET search_path TO price_tracker, public; DELETE FROM listings WHERE website = 'test-site'; DELETE FROM searches WHERE website = 'test-site';\" >/dev/null 2>&1"

echo ""
echo "============================================="
echo -e "${YELLOW}📊 Integration Test Results Summary${NC}"
echo "============================================="
echo -e "Total tests run: ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All integration tests passed! Database schema is working correctly.${NC}"
    echo ""
    echo -e "${BLUE}✅ Schema Features Verified:${NC}"
    echo "  - Database connectivity"
    echo "  - Schema creation and isolation"
    echo "  - Table structure and constraints"
    echo "  - Index creation and usage"
    echo "  - Data insertion (rich and minimal)"
    echo "  - Data retrieval and querying"
    echo "  - Data type validation"
    echo "  - Cleanup operations"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some integration tests failed. Check the database setup.${NC}"
    exit 1
fi 