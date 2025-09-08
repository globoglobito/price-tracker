# Price Tracker Component Diagram

## Simplified Component Overview

This diagram shows the key components and their relationships in a simplified view.

```mermaid
graph LR
    %% External
    eBay[eBay]
    User[User]
    
    %% Core Components
    subgraph System["Price Tracker System"]
        API[FastAPI API]
        DB[(PostgreSQL)]
        Queue[(RabbitMQ)]
        
        subgraph Scraping["Scraping Components"]
            Collector[Collector<br/>Job]
            Workers[16x Workers<br/>Jobs]
        end
    end
    
    %% Data Flow
    eBay -->|Search Results| Collector
    Collector -->|Queue Listings| Queue
    Collector -->|Store Metadata| DB
    
    Queue -->|Distribute Work| Workers
    Workers -->|Enrich Data| eBay
    Workers -->|Save Results| DB
    
    User -->|API Requests| API
    API -->|Query Data| DB
    
    %% Styling
    classDef external fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef core fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef scraping fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class eBay,User external
    class API,DB,Queue core
    class Collector,Workers scraping
```

## Component Responsibilities

### 🌐 **External Systems**
- **eBay**: Source of search results and listing data
- **User**: API consumers and data query users

### 🏗️ **Core Infrastructure**
- **FastAPI**: REST API for data access and queries
- **PostgreSQL**: Primary data storage for all collected information
- **RabbitMQ**: Message queue for work distribution and coordination

### 🔄 **Scraping Components**
- **Collector Job**: Scrapes search results and initiates processing pipeline
- **Worker Jobs**: 16 parallel workers that enrich individual listings

## Data Processing Pipeline

```mermaid
sequenceDiagram
    participant C as Collector Job
    participant Q as RabbitMQ
    participant W as Worker Jobs (16x)
    participant E as eBay
    participant D as PostgreSQL
    
    Note over C,D: Collection Phase
    C->>E: 1. Scrape search results
    E-->>C: 2. Return listing metadata
    C->>D: 3. Store search metadata
    C->>Q: 4. Queue listings for enrichment
    
    Note over Q,D: Processing Phase
    Q->>W: 5. Distribute work to workers
    W->>E: 6. Fetch individual listing pages
    E-->>W: 7. Return detailed listing data
    W->>D: 8. Store enriched data
    
    Note over C,D: Result
    Note right of D: All data available via API
```

## Performance Metrics

| Component | Capacity | Performance |
|-----------|----------|-------------|
| **Collector** | 1 job | ~100 listings/minute |
| **Workers** | 16 parallel | ~16 listings/minute each |
| **Queue** | Unlimited | Message persistence + TTL |
| **Database** | Persistent | ACID transactions |
| **API** | Multiple users | RESTful queries |

## Scalability Options

### 🔧 **Horizontal Scaling**
- **Workers**: Increase `WORKER_PARALLELISM` for more concurrent processing
- **API**: Scale FastAPI deployment replicas
- **Queue**: RabbitMQ clustering for high availability

### 📈 **Vertical Scaling**
- **Resources**: Increase CPU/memory limits for all components
- **Storage**: Expand PostgreSQL and RabbitMQ storage
- **Network**: Optimize bandwidth for high-volume scraping

## Deployment Architecture

```mermaid
graph TB
    subgraph K8s["Kubernetes Cluster"]
        subgraph Namespace["price-tracker namespace"]
            subgraph Pods["Pods"]
                APIPod[FastAPI Pod]
                DBPod[PostgreSQL Pod]
                QueuePod[RabbitMQ Pod]
                CollectorPod[Collector Job Pod]
                WorkerPods[Worker Job Pods<br/>16x instances]
            end
            
            subgraph Storage["Persistent Volumes"]
                DBVol[Database Volume<br/>8Gi]
                QueueVol[Queue Volume<br/>2Gi]
                SnapVol[Snapshots Volume<br/>10Gi]
            end
        end
    end
    
    subgraph External["External Access"]
        NodePort[NodePort :30080]
        HostPath[Host Path Mounts]
    end
    
    APIPod --> NodePort
    DBPod --> DBVol
    QueuePod --> QueueVol
    WorkerPods --> SnapVol
    WorkerPods --> HostPath
    
    classDef pod fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef volume fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef external fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    
    class APIPod,DBPod,QueuePod,CollectorPod,WorkerPods pod
    class DBVol,QueueVol,SnapVol volume
    class NodePort,HostPath external
```
