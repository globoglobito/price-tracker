# Helm Commands for Price Tracker PostgreSQL

# Install PostgreSQL using Bitnami Helm Chart
# First, add the Bitnami repository if not already added
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL with custom values
helm install price-tracker-postgres bitnami/postgresql \
  -f helm/price-tracker-postgres-values.yaml \
  --namespace default \
  --create-namespace

# Alternative: Install with inline values
helm install price-tracker-postgres bitnami/postgresql \
  --set auth.postgresPassword=price_tracker_admin_password \
  --set auth.username=price_tracker_user \
  --set auth.password=price_tracker_password \
  --set auth.database=price_tracker_db \
  --set primary.persistence.enabled=true \
  --set primary.persistence.size=8Gi \
  --set primary.persistence.storageClass=microk8s-hostpath \
  --namespace default

# Check the status
helm status price-tracker-postgres

# Get the PostgreSQL password
export POSTGRES_PASSWORD=$(kubectl get secret --namespace default price-tracker-postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)

# Connect to PostgreSQL (from within the cluster)
kubectl run price-tracker-postgres-postgresql-client --rm --tty -i --restart='Never' \
  --namespace default \
  --image docker.io/bitnami/postgresql:15 \
  --env="PGPASSWORD=$POSTGRES_PASSWORD" \
  --command -- psql --host price-tracker-postgres-postgresql --port 5432 -U postgres -d price_tracker_db

# Port-forward to access PostgreSQL from localhost
kubectl port-forward --namespace default svc/price-tracker-postgres-postgresql 5432:5432 &
PGPASSWORD="$POSTGRES_PASSWORD" psql --host 127.0.0.1 --port 5432 --username postgres --dbname price_tracker_db

# Upgrade the installation
helm upgrade price-tracker-postgres bitnami/postgresql \
  -f helm/price-tracker-postgres-values.yaml \
  --namespace default

# Uninstall
helm uninstall price-tracker-postgres --namespace default

# List all Helm releases
helm list --all-namespaces
