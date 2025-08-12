#!/bin/bash
# Price Tracker Secrets Quick Reference
# Run this script to see what secrets you need to create

echo "🔐 Price Tracker - Required Kubernetes Secrets"
echo "=============================================="
echo ""
echo "Before deploying, you must create these required secrets in the 'price-tracker' namespace:"
echo ""

echo "1️⃣  postgres-secret (Database credentials - required)"
echo "   kubectl create secret generic postgres-secret \\"
echo "     --from-literal=POSTGRES_USER=price_tracker_user \\"
echo "     --from-literal=POSTGRES_PASSWORD=YOUR_DB_PASSWORD \\"
echo "     --from-literal=POSTGRES_DB=price_tracker_db \\"
echo "     -n price-tracker"
echo ""

echo "2️⃣  docker-registry-secret (Docker Hub access - required)"
echo "   kubectl create secret docker-registry docker-registry-secret \\"
echo "     --docker-server=https://index.docker.io/v1/ \\"
echo "     --docker-username=YOUR_DOCKERHUB_USERNAME \\"
echo "     --docker-password=YOUR_DOCKERHUB_PASSWORD \\"
echo "     --docker-email=YOUR_EMAIL \\"
echo "     -n price-tracker"
echo ""

echo "3️⃣  price-tracker-postgres-credentials (Optional - only if using Bitnami Helm PostgreSQL)"
echo "4️⃣  scraper-proxy (Optional - only if you need an outbound proxy)"
echo "   kubectl create secret generic scraper-proxy \\" 
echo "     --from-literal=http_proxy=http://user:pass@host:port \\" 
echo "     --from-literal=https_proxy=http://user:pass@host:port \\" 
echo "     -n price-tracker"
echo ""
echo "   kubectl create secret generic price-tracker-postgres-credentials \\"
echo "     --from-literal=postgres-password=YOUR_DB_PASSWORD \\"
echo "     --from-literal=password=YOUR_DB_PASSWORD \\"
echo "     -n price-tracker"
echo ""

echo "💡 Tips:"
echo "   • Replace YOUR_* placeholders with actual values"
echo "   • Use the same password for all database-related secrets"
echo "   • Generate strong passwords: openssl rand -base64 24"
echo "   • See docs/SECRETS.md for complete setup guide"
echo ""

echo "✅ Verify secrets after creation:"
echo "   kubectl get secrets -n price-tracker"
echo ""

echo "🚀 Deploy after required secrets are created:"
echo "   ./scripts/deploy-complete.sh"
echo ""

# Check if secrets already exist
if command -v kubectl &> /dev/null; then
    echo "🔍 Current secret status:"
    if kubectl get namespace price-tracker &> /dev/null; then
        echo "   Namespace: ✅ exists"
        
        secrets=("postgres-secret" "docker-registry-secret" "price-tracker-postgres-credentials" "scraper-proxy")
        for secret in "${secrets[@]}"; do
            if kubectl get secret "$secret" -n price-tracker &> /dev/null; then
                echo "   $secret: ✅ exists"
            else
                echo "   $secret: ❌ missing"
            fi
        done
    else
        echo "   Namespace: ❌ price-tracker namespace not found"
        echo "   Create it first: kubectl create namespace price-tracker"
    fi
    echo ""
fi
