#!/bin/bash
# Setup script for Price Tracker Grafana Dashboard
# This script imports the comprehensive dashboard and configures data sources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Setting up Price Tracker Grafana Dashboard${NC}"
echo "=============================================="

# Check if Grafana is accessible
echo -e "${YELLOW}📡 Checking Grafana connectivity...${NC}"
if ! curl -s http://localhost:3000/api/health > /dev/null; then
    echo -e "${RED}❌ Grafana is not accessible at http://localhost:3000${NC}"
    echo "Please ensure Grafana is running and port forwarding is active:"
    echo "microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80"
    exit 1
fi
echo -e "${GREEN}✅ Grafana is accessible${NC}"

# Get Grafana admin credentials
echo -e "${YELLOW}🔐 Getting Grafana admin credentials...${NC}"
GRAFANA_PASSWORD=$(microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d)
echo -e "${GREEN}✅ Credentials retrieved${NC}"

# Create data sources
echo -e "${YELLOW}📊 Setting up data sources...${NC}"

# PostgreSQL Data Source
echo "Creating PostgreSQL data source..."
curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:${GRAFANA_PASSWORD}" \
  -d '{
    "name": "PostgreSQL",
    "type": "postgres",
    "url": "postgres-service.price-tracker.svc.cluster.local:5432",
    "database": "price_tracker_db",
    "user": "admin",
    "secureJsonData": {
      "password": "devhub"
    },
    "jsonData": {
      "sslmode": "disable",
      "maxOpenConns": 0,
      "maxIdleConns": 2,
      "connMaxLifetime": 14400
    },
    "access": "proxy",
    "isDefault": false
  }' \
  http://localhost:3000/api/datasources

echo -e "${GREEN}✅ PostgreSQL data source created${NC}"

# Prometheus Data Source (should already exist)
echo "Checking Prometheus data source..."
PROMETHEUS_DS=$(curl -s -u "admin:${GRAFANA_PASSWORD}" http://localhost:3000/api/datasources | jq -r '.[] | select(.type=="prometheus") | .uid')

if [ "$PROMETHEUS_DS" = "null" ] || [ -z "$PROMETHEUS_DS" ]; then
    echo "Creating Prometheus data source..."
    curl -X POST \
      -H "Content-Type: application/json" \
      -u "admin:${GRAFANA_PASSWORD}" \
      -d '{
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "uid": "prometheus"
      }' \
      http://localhost:3000/api/datasources
    echo -e "${GREEN}✅ Prometheus data source created${NC}"
else
    echo -e "${GREEN}✅ Prometheus data source already exists${NC}"
fi

# Import Dashboard
echo -e "${YELLOW}📈 Importing Price Tracker dashboard...${NC}"
# Create properly formatted JSON for import
echo '{"dashboard":' > /tmp/dashboard-import.json
cat grafana/price-tracker-dashboard.json >> /tmp/dashboard-import.json
echo '}' >> /tmp/dashboard-import.json

curl -X POST \
  -H "Content-Type: application/json" \
  -u "admin:${GRAFANA_PASSWORD}" \
  -d @/tmp/dashboard-import.json \
  http://localhost:3000/api/dashboards/db

echo -e "${GREEN}✅ Dashboard imported successfully${NC}"

echo ""
echo -e "${GREEN}🎉 Price Tracker Dashboard Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📊 Access your dashboard at:${NC}"
echo "   http://localhost:3000/d/price-tracker-dashboard/price-tracker-comprehensive-dashboard"
echo ""
echo -e "${BLUE}🔑 Login credentials:${NC}"
echo "   Username: admin"
echo "   Password: ${GRAFANA_PASSWORD}"
echo ""
echo -e "${BLUE}📋 Dashboard includes:${NC}"
echo "   • Queue Status (RabbitMQ messages)"
echo "   • Active Workers count"
echo "   • Listings scraped over time"
echo "   • Listings by condition and brand"
echo "   • Price trends and statistics"
echo "   • Scraping rate metrics"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   • Dashboard refreshes every 30 seconds"
echo "   • Time range is set to last 24 hours"
echo "   • All panels use PostgreSQL queries for real-time data"
echo "   • Prometheus metrics for system monitoring"
