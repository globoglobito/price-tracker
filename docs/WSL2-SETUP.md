# WSL2 + MicroK8s Setup and Optimization Guide (No Local Docker)

This guide covers WSL2-specific optimizations and troubleshooting for the Price Tracker project using GitHub Actions for image building and MicroK8s for local deployment.

## Project Architecture

- **Image Building**: GitHub Actions → Docker Hub (no local Docker needed)
- **Local Deployment**: WSL2 + MicroK8s pulls images from Docker Hub
- **Database**: PostgreSQL via Bitnami Helm chart
- **Secrets**: Kubernetes secrets for all credentials

## WSL2 Setup and Optimization

### Initial WSL2 Configuration

1. **Optimize WSL2 Memory and CPU**:
   Create or edit `%USERPROFILE%\.wslconfig`:
   ```ini
   [wsl2]
   memory=4GB
   processors=2
   swap=2GB
   localhostForwarding=true
   ```

2. **Restart WSL2**:
   ```bash
   # From Windows Command Prompt or PowerShell
   wsl --shutdown
   wsl
   ```

### MicroK8s Installation and Configuration

1. **Install MicroK8s in WSL2**:
   ```bash
   sudo snap install microk8s --classic
   sudo usermod -a -G microk8s $USER
   sudo chown -f -R $USER ~/.kube
   newgrp microk8s
   ```

2. **Enable Required Addons**:
   ```bash
   microk8s enable dns storage registry helm3
   microk8s status --wait-ready
   ```

3. **Create kubectl alias**:
   ```bash
   sudo snap alias microk8s.kubectl kubectl
   echo "alias kubectl='microk8s kubectl'" >> ~/.bashrc
   ```

4. **Configure kubectl for Windows access**:
   ```bash
   # Export kubeconfig for use in Windows
   microk8s config > ~/.kube/config
   
   # Make it accessible from Windows (if needed)
   cp ~/.kube/config /mnt/c/Users/$USER/.kube/config
   ```

## Docker Hub Integration (No Local Docker)

### GitHub Actions → Docker Hub → MicroK8s Flow

1. **Code Push** triggers GitHub Actions
2. **GitHub Actions** builds and pushes image to Docker Hub
3. **MicroK8s** pulls image from Docker Hub using `docker-registry-secret`

### Setup Docker Hub Secret in Kubernetes

```bash
# Create Docker Hub secret for image pulls
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=docker.io \
  --docker-username=globoglobitos \
  --docker-password=YOUR_DOCKER_HUB_TOKEN \
  --docker-email=your-email@example.com

# Label for better organization
kubectl label secret docker-registry-secret \
  app=price-tracker \
  project=price-tracker
```

### Verify Image Pull Access

```bash
# Test image pull
kubectl run test-pull --image=globoglobitos/price-tracker:latest --rm=true --restart=Never --command -- echo "Image pull successful"
```

## Storage Optimization

### MicroK8s Storage Configuration

1. **Check storage class**:
   ```bash
   kubectl get storageclass
   ```

2. **Optimize hostpath storage for WSL2**:
   ```bash
   # Create dedicated directory for K8s storage
   sudo mkdir -p /var/snap/microk8s/common/default-storage
   sudo chown -R $USER:$USER /var/snap/microk8s/common/default-storage
   ```

3. **Monitor disk usage**:
   ```bash
   df -h
   du -sh /var/snap/microk8s/common/default-storage
   ```

## Networking in WSL2

### Port Forwarding and Access

1. **Access services from Windows**:
   ```bash
   # Port forward from WSL2 to Windows
   kubectl port-forward service/price-tracker-service 8080:80
   # Access from Windows: http://localhost:8080
   ```

2. **Get WSL2 IP address**:
   ```bash
   ip addr show eth0 | grep inet
   ```

3. **Windows firewall configuration** (if needed):
   ```powershell
   # Allow WSL2 ports through Windows firewall
   New-NetFirewallRule -DisplayName "WSL2" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
   ```

## Performance Optimization

### WSL2 Resource Management

1. **Monitor resource usage**:
   ```bash
   # Memory usage
   free -h
   
   # CPU usage
   top
   
   # Disk I/O
   iotop
   ```

2. **Optimize PostgreSQL for WSL2**:
   The Helm values already include WSL2 optimizations:
   ```yaml
   configuration: |
     shared_buffers = 128MB
     effective_cache_size = 256MB
     work_mem = 4MB
     maintenance_work_mem = 64MB
     max_connections = 100
   ```

### Container Optimizations

1. **Use multi-stage builds** (when building your app):
   ```dockerfile
   # Use Alpine for smaller images
   FROM python:3.11-alpine
   
   # Optimize for WSL2
   ENV PYTHONUNBUFFERED=1
   ENV PYTHONDONTWRITEBYTECODE=1
   ```

## Troubleshooting Common Issues

### MicroK8s Issues

1. **MicroK8s not starting**:
   ```bash
   sudo microk8s stop
   sudo microk8s start
   microk8s status --wait-ready
   ```

2. **DNS resolution problems**:
   ```bash
   microk8s disable dns
   microk8s enable dns
   ```

3. **Storage issues**:
   ```bash
   # Check storage addon
   microk8s status
   
   # Reset storage if needed
   microk8s disable storage
   microk8s enable storage
   ```

### Pod/Container Issues

1. **Image pull failures**:
   ```bash
   # Check if docker-registry-secret exists
   kubectl get secret docker-registry-secret
   
   # Recreate if needed
   kubectl create secret docker-registry docker-registry-secret \
     --docker-server=docker.io \
     --docker-username=globoglobitos \
     --docker-password=YOUR_DOCKER_HUB_TOKEN
   ```

2. **Persistent volume issues**:
   ```bash
   # Check PV/PVC status
   kubectl get pv,pvc
   
   # Check node storage
   df -h /var/snap/microk8s/common/default-storage
   ```

3. **Pod scheduling issues**:
   ```bash
   # Check node status
   kubectl get nodes
   kubectl describe node
   
   # Check resource quotas
   kubectl describe quota
   ```

### Database Connection Issues

1. **PostgreSQL not accessible**:
   ```bash
   # Check PostgreSQL pod status
   kubectl get pods -l app=postgres
   kubectl logs -l app=postgres
   
   # Test connection from within cluster
   kubectl run test-postgres --rm -i --tty \
     --image postgres:15-alpine -- \
     psql -h postgres-service -U price_tracker_user -d price_tracker_db
   ```

2. **Secret/credential issues**:
   ```bash
   # Verify secrets exist
   kubectl get secrets
   
   # Check secret content (base64 decoded)
   kubectl get secret postgres-secret -o yaml
   ```

## WSL2 Backup and Recovery

### Backup Strategy

1. **Export WSL2 distribution**:
   ```bash
   # From Windows Command Prompt or PowerShell
   wsl --export Ubuntu-22.04 C:\wsl-backup\ubuntu-backup.tar
   ```

2. **Backup Kubernetes data**:
   ```bash
   # Backup persistent volumes
   sudo tar -czf k8s-data-backup.tar.gz /var/snap/microk8s/common/default-storage
   
   # Backup configurations
   kubectl get all -o yaml > cluster-backup.yaml
   ```

### Recovery

1. **Import WSL2 distribution**:
   ```bash
   # From Windows Command Prompt or PowerShell
   wsl --import Ubuntu-22.04-restored C:\wsl\ubuntu C:\wsl-backup\ubuntu-backup.tar
   ```

2. **Restore Kubernetes data**:
   ```bash
   sudo tar -xzf k8s-data-backup.tar.gz -C /
   kubectl apply -f cluster-backup.yaml
   ```

## Monitoring and Maintenance

### Regular Maintenance Tasks

1. **Clean up Kubernetes resources**:
   ```bash
   # Clean unused images from MicroK8s
   microk8s ctr images list | grep -v registry.k8s.io | awk '{print $1}' | xargs microk8s ctr images rm
   
   # Clean completed pods
   kubectl delete pods --field-selector=status.phase==Succeeded
   ```

2. **Monitor WSL2 disk usage**:
   ```bash
   # Check WSL2 virtual disk size
   ls -lh /mnt/c/Users/$USER/AppData/Local/Packages/*/LocalState/ext4.vhdx
   ```

3. **Update components**:
   ```bash
   # Update MicroK8s
   sudo snap refresh microk8s
   
   # Update Helm repositories
   helm repo update
   ```

## Integration with Windows Development

### VS Code Integration

1. **Install WSL extension** in VS Code
2. **Connect to WSL2**: `Ctrl+Shift+P` → "WSL: Connect to WSL"
3. **Install Kubernetes extension** in WSL2 VS Code

### Windows Terminal Integration

1. **Use Windows Terminal** with WSL2 profile
2. **Run kubectl commands** from Windows Command Prompt or PowerShell:
   ```bash
   wsl kubectl get pods
   ```

This guide should help you optimize and troubleshoot your WSL2 + MicroK8s environment for the Price Tracker project!
