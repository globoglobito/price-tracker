#!/bin/bash
# Database Migration Script for Price Tracker
# Applies SQL migrations to PostgreSQL database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Database connection parameters (from environment or defaults)
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"price_tracker_db"}
DB_USER=${DB_USER:-"admin"}

echo -e "${BLUE}🗄️  Applying Database Migration${NC}"
echo "====================================="

# Use microk8s kubectl for all operations
KUBECTL="microk8s kubectl"

# Check if PostgreSQL pod is running
if ! $KUBECTL get pod -n price-tracker -l app=postgres | grep -q Running; then
    echo -e "${RED}❌ PostgreSQL pod is not running${NC}"
    echo "Make sure the database is running and accessible"
    exit 1
fi

# Check if we can connect to the database
if ! $KUBECTL exec -n price-tracker deployment/postgres -- pg_isready -U $DB_USER -d $DB_NAME >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to PostgreSQL database${NC}"
    echo "Make sure the database is running and accessible"
    exit 1
fi

echo -e "${GREEN}✅ Database connection successful${NC}"

# Apply the migration
echo -e "${YELLOW}📝 Applying migration: 001_initial_schema.sql${NC}"

# Copy migration file to pod and execute it
$KUBECTL cp database/migrations/001_initial_schema.sql price-tracker/$(microk8s kubectl get pod -n price-tracker -l app=postgres -o jsonpath='{.items[0].metadata.name}'):/tmp/migration.sql
$KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -f /tmp/migration.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration applied successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔍 Verifying tables created...${NC}"

# Verify tables were created
TABLES=$($KUBECTL exec -n price-tracker deployment/postgres -- psql -U $DB_USER -d $DB_NAME -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'price_tracker' AND table_name IN ('searches', 'listings');")

if echo "$TABLES" | grep -q "searches" && echo "$TABLES" | grep -q "listings"; then
    echo -e "${GREEN}✅ Tables 'searches' and 'listings' created successfully${NC}"
else
    echo -e "${RED}❌ Tables not found after migration${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Database schema setup complete!${NC}"
echo "====================================="
echo "Tables created:"
echo "  - searches (user-defined search terms)"
echo "  - listings (scraped listing data)"
echo ""
echo "Ready for the next step in the price tracker development!" 