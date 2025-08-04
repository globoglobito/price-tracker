#!/bin/bash
# Price Tracker Deployment Script for MicroK8s

set -e

echo "🚀 Deploying Price Tracker to MicroK8s..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    echo "   For MicroK8s, use: microk8s kubectl"
    exit 1
fi

# Function to apply manifests with retry
apply_with_retry() {
    local file=$1
    local retries=3
    local delay=5
    
    for i in $(seq 1 $retries); do
        if kubectl apply -f "$file" --validate=false; then
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
kubectl create namespace price-tracker --dry-run=client -o yaml | kubectl apply -f - || kubectl get namespace price-tracker &>/dev/null && echo "✅ Namespace already exists"

# Apply configurations in order
echo "🔧 Applying configurations..."
apply_with_retry "k8s/secrets.yaml"
apply_with_retry "k8s/configmaps.yaml"
apply_with_retry "k8s/postgres-values.yaml"

echo "🗄️  Deploying database..."
apply_with_retry "k8s/manifests/db-deployment.yaml"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

echo "🌐 Deploying application..."
apply_with_retry "k8s/deployment.yaml"
apply_with_retry "k8s/service.yaml"
apply_with_retry "k8s/manifests/app-deployment.yaml"

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
kubectl wait --for=condition=ready pod -l app=price-tracker --timeout=300s

echo "📊 Deployment status:"
kubectl get pods,services,pvc -l project=price-tracker

echo ""
echo "🎉 Price Tracker deployed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Check pod logs: kubectl logs -l app=price-tracker"
echo "   2. Port forward to access the app: kubectl port-forward service/price-tracker-service 8080:80"
echo "   3. Access the application at: http://localhost:8080"
echo ""
echo "🔍 Useful commands:"
echo "   - View all resources: kubectl get all -l project=price-tracker"
echo "   - Check database: kubectl exec -it deployment/postgres -- psql -U price_tracker_user -d price_tracker_db"
echo "   - View logs: kubectl logs -f deployment/price-tracker"
