# Monitoring and Observability Guide

This document provides comprehensive instructions for monitoring the Price Tracker application using Grafana, Prometheus, and other observability tools.

## 📊 Overview

The Price Tracker application includes a complete observability stack with:
- **Grafana** - Dashboards and visualization
- **Prometheus** - Metrics collection and storage
- **Loki** - Log aggregation
- **Tempo** - Distributed tracing
- **Alertmanager** - Alerting and notifications

## 🚀 Quick Start

### 1. Enable Observability Stack
```bash
# Enable the complete observability stack
microk8s enable observability
```

### 2. Access Grafana
```bash
# Port forward to access Grafana
microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80

```

### 3. Get Admin Password
```bash
# Get the actual admin password from Kubernetes secret
microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

## 🔧 Components

### Grafana
- **Purpose**: Dashboards and visualization
- **Access**: http://localhost:3000 (after port forwarding)
- **Credentials**: admin / prom-operator
- **Namespace**: observability

### Prometheus
- **Purpose**: Metrics collection and storage
- **Access**: http://localhost:9090 (after port forwarding)
- **Namespace**: observability

### Loki
- **Purpose**: Log aggregation and search
- **Access**: Integrated with Grafana
- **Namespace**: observability

### Tempo
- **Purpose**: Distributed tracing
- **Access**: Integrated with Grafana
- **Namespace**: observability

## 📈 Monitoring Price Tracker

### Application Metrics
The Price Tracker application exposes metrics for:
- **Scraper Performance**: Pages scraped, listings processed, errors
- **Queue Status**: Messages in queue, processing rate, dead letter queue
- **Database Performance**: Query times, connection pool status
- **Worker Status**: Active workers, processing time, success/failure rates

### Key Dashboards

#### 1. **Saxophone Market Intelligence Dashboard** (Primary Business Dashboard)
**URL**: http://localhost:3000/d/saxophone-market-dashboard/saxophone-market-intelligence-dashboard

**Business Insights Provided**:
- **Saxophone Types Distribution**: Alto, Tenor, Soprano, Baritone, Bass, C-Melody breakdown
- **Geographic Market Analysis**: Seller locations by country with market penetration
- **Price Analysis by Type**: Average prices for each saxophone type
- **Brand Performance**: Top brands by listing count and average price
- **Market Price Range**: Min/Max prices to identify market opportunities
- **Geographic Price Variations**: Price differences by country/region

**Key Business Questions Answered**:
- Which saxophone types are most popular in the market?
- What are the price ranges for different saxophone types?
- Which countries have the most saxophone listings?
- What brands command the highest prices?
- Where are the best deals located geographically?

#### 2. **Technical Monitoring Dashboard** (System Health)
**URL**: http://localhost:3000/d/price-tracker-dashboard/price-tracker-comprehensive-dashboard

**Technical Metrics**:
- **Queue Status**: RabbitMQ message counts and processing rates
- **Active Workers**: Number of running worker pods
- **Scraping Performance**: Listings processed over time
- **System Health**: Database connections, error rates

## 💼 Business Intelligence Insights

### Market Analysis Capabilities

The **Saxophone Market Intelligence Dashboard** provides actionable business insights:

#### **Market Segmentation**
- **Saxophone Types**: Identify which types (Alto, Tenor, Soprano, etc.) dominate the market
- **Price Tiers**: Understand price ranges for different saxophone types
- **Geographic Markets**: See which countries have the most listings and best prices

#### **Competitive Intelligence**
- **Brand Analysis**: Track which brands have the most listings and highest prices
- **Price Positioning**: Compare average prices across brands and types
- **Market Opportunities**: Identify price gaps and underserved markets

#### **Operational Insights**
- **Inventory Trends**: Track listing volume over time
- **Price Fluctuations**: Monitor price changes and market volatility
- **Geographic Distribution**: Understand global market reach

### Key Performance Indicators (KPIs)

**Market Penetration**:
- Total listings processed
- Geographic coverage (countries with listings)
- Saxophone type diversity

**Price Intelligence**:
- Average market price
- Price range (min/max)
- Price trends over time

**Brand Performance**:
- Top brands by volume
- Premium brand identification
- Market share analysis

### Business Decision Support

**For Buyers**:
- Find best deals by saxophone type and location
- Identify price trends for timing purchases
- Compare prices across brands and conditions

**For Sellers**:
- Understand market pricing for different saxophone types
- Identify geographic markets with higher prices
- Track competitive positioning

**For Market Analysis**:
- Monitor market trends and seasonality
- Identify emerging brands or types
- Track global market dynamics

## 🔍 Troubleshooting

### Common Issues

1. **Node Exporter Error**:
   ```
   CreateContainerError: path "/" is mounted on "/" but it is not a shared or slave mount
   ```
   **Solution**: This is a known WSL2 issue. It doesn't affect Grafana functionality.

2. **Grafana Not Accessible**:
   ```bash
   # Check if Grafana pod is running
   microk8s kubectl get pods -n observability | grep grafana
   
   # Restart port forwarding
   microk8s kubectl port-forward -n observability svc/kube-prom-stack-grafana 3000:80
   ```

3. **Prometheus Not Collecting Metrics**:
   ```bash
   # Check Prometheus pod status
   microk8s kubectl get pods -n observability | grep prometheus
   
   # Check Prometheus targets
   # Access Prometheus UI and go to Status > Targets
   ```

## 📊 Custom Dashboards

### Creating Price Tracker Dashboards

1. **Access Grafana**: http://localhost:3000
2. **Create Dashboard**: Click "+" > "Dashboard"
3. **Add Panels**: Configure panels for:
   - Scraper metrics
   - Queue status
   - Database performance
   - Worker health

### Sample Queries

**Queue Messages**:
```promql
rabbitmq_queue_messages{queue="listing_enrichment"}
```

**Worker Processing Rate**:
```promql
rate(scraper_worker_processed_total[5m])
```

**Database Connections**:
```promql
pg_stat_database_numbackends
```

## 🚨 Alerting

### Setting Up Alerts

1. **Access Alertmanager**: http://localhost:9093 (after port forwarding)
2. **Configure Rules**: Create alerting rules for:
   - High error rates
   - Queue backup
   - Database connection issues
   - Worker failures

### Sample Alert Rules

**High Error Rate**:
```yaml
groups:
- name: price-tracker
  rules:
  - alert: HighErrorRate
    expr: rate(scraper_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
```

## 🔐 Security

### Access Control
- Grafana admin credentials are stored in Kubernetes secrets
- Access is restricted to localhost via port forwarding
- No external exposure by default

### Secret Management
```bash
# Get Grafana admin password
microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d

# Update Grafana password
microk8s kubectl patch secret -n observability kube-prom-stack-grafana --type='json' -p='[{"op": "replace", "path": "/data/admin-password", "value": "'$(echo -n "new_password" | base64)'"}]'
```

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [MicroK8s Observability](https://microk8s.io/docs/addon-observability)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)

OK 
