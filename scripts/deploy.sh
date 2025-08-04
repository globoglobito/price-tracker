#!/bin/bash
# Price Tracker Deployment Script for MicroK8s

set -e

echo "🚀 Deploying Price Tracker to MicroK8s..."

# Check if microk8s kubectl is available
if ! command -v microk8s &> /dev/null; then
    echo "❌ microk8s is not installed or not in PATH"
    exit 1
fi

# Use microk8s kubectl for all operations
KUBECTL="microk8s kubectl"

# Function to apply manifests with retry
apply_with_retry() {
    local file=$1
    local retries=3
    local delay=5
    
    for i in $(seq 1 $retries); do
        if $KUBECTL apply -f "$file" -n price-tracker; then
            echo "✅ Applied $file successfully"
            return 0
        else
            echo "⚠️  Failed to apply $file, attempt $i/$retries"
            if [ $i -lt $retries ]; then
                echo "   Retrying in ${delay}s..."
                sleep $delay
            fi
        fi
    done
    
    echo "❌ Failed to apply $file after $retries attempts"
    return 1
}

# Create namespace if it doesn't exist
echo "📁 Creating namespace..."
$KUBECTL create namespace price-tracker --dry-run=client -o yaml | $KUBECTL apply -f - || $KUBECTL get namespace price-tracker &>/dev/null && echo "✅ Namespace already exists"

# Apply configurations in order
echo "🔧 Applying configurations..."
echo "ℹ️  Skipping secrets.yaml (secrets should be created manually first)"
apply_with_retry "k8s/configmaps.yaml"
apply_with_retry "k8s/postgres-values.yaml"

echo "🗄️  Deploying database..."
apply_with_retry "k8s/manifests/db-deployment.yaml"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
$KUBECTL wait --for=condition=ready pod -l app=postgres -n price-tracker --timeout=300s

echo "🌐 Deploying application..."
apply_with_retry "k8s/service.yaml"
apply_with_retry "k8s/manifests/app-deployment.yaml"

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
if $KUBECTL wait --for=condition=ready pod -l app=price-tracker -n price-tracker --timeout=120s; then
    echo "✅ Application is ready!"
else
    echo "⚠️  Application readiness timeout reached. Checking pod status..."
    $KUBECTL get pods -l app=price-tracker -n price-tracker
    echo "📋 Pod details:"
    $KUBECTL describe pod -l app=price-tracker -n price-tracker | tail -20
    echo "⚠️  Continuing deployment despite timeout..."
fi

echo "📊 Deployment status:"
$KUBECTL get pods,services,pvc -l project=price-tracker -n price-tracker

echo ""
echo "🎉 Price Tracker deployed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Check pod logs: $KUBECTL logs -l app=price-tracker"
echo "   2. Port forward to access the app: $KUBECTL port-forward service/price-tracker-service 8080:80"
echo "   3. Access the application at: http://localhost:8080"
echo ""
echo "🔍 Useful commands:"
echo "   - View all resources: $KUBECTL get all -l project=price-tracker"
echo "   - Check database: $KUBECTL exec -it deployment/postgres -- psql -U admin -d price_tracker_db"
echo "   - View logs: $KUBECTL logs -f deployment/price-tracker"
