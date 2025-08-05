# Database Schema Documentation

## Overview

This directory contains the database schema and migrations for the Price Tracker application. The schema is designed to be flexible and handle various levels of data richness from different websites.

## Schema Design

### Core Philosophy

- **Flexible Data Structure**: Handles both data-rich sites (eBay, Reverb) and data-poor sites (simple shops)
- **Append-Only Strategy**: Each scrape creates new records for historical price tracking
- **Scalable Design**: Supports pod-per-search-term architecture

### Tables

#### `searches` Table
Stores user-defined search terms for different websites.

```sql
CREATE TABLE price_tracker.searches (
    id SERIAL PRIMARY KEY,
    search_term VARCHAR(200) NOT NULL,
    website VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(search_term, website)
);
```

**Fields:**
- `search_term`: The search query (e.g., "Selmer Mark VI")
- `website`: Target website (e.g., "ebay", "reverb")
- `is_active`: Whether this search should continue running
- `created_at/updated_at`: Timestamps for tracking

#### `listings` Table
Stores scraped listings with flexible data structure.

```sql
CREATE TABLE price_tracker.listings (
    id SERIAL PRIMARY KEY,
    
    -- Core required fields (always available)
    listing_name VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    url TEXT NOT NULL,
    website VARCHAR(100) NOT NULL,
    scraped_at TIMESTAMP NOT NULL,
    
    -- Optional fields (site-dependent, can be NULL)
    brand VARCHAR(100),
    model VARCHAR(100),
    type VARCHAR(50),
    date_listed DATE,
    location VARCHAR(200),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Required Fields:**
- `listing_name`: Title/name of the listing
- `price`: Current price
- `url`: Direct link to listing
- `website`: Source website
- `scraped_at`: When data was scraped

**Optional Fields:**
- `brand`: Item brand (e.g., "Yamaha", "Selmer")
- `model`: Specific model (e.g., "Mark VI", "YTS-61")
- `type`: Saxophone type (e.g., "Tenor", "Alto")
- `date_listed`: When listing was created
- `location`: Item location

## Usage Examples

### Data-Rich Site (eBay)
```sql
INSERT INTO price_tracker.listings (
    listing_name, price, url, website, scraped_at,
    brand, model, type, date_listed, location
) VALUES (
    'YAMAHA YTS-61S Tenor Saxophone', 2400.00,
    'https://www.ebay.com/itm/357413100867', 'ebay', NOW(),
    'Yamaha', 'YTS-61S', 'Tenor', '2024-01-15', 'Fukuoka Ken, Japan'
);
```

### Data-Poor Site (Simple Shop)
```sql
INSERT INTO price_tracker.listings (
    listing_name, price, url, website, scraped_at
) VALUES (
    'Saxophone for Sale', 500.00,
    'https://example-shop.com/saxophone-123', 'example-shop', NOW()
);
```

## Migrations

### Applying Migrations

```bash
# Apply the initial schema
./database/apply_migration.sh
```

### Testing the Schema

```bash
# Run comprehensive integration tests
./database/test_integration.sh

# Or test with sample data only
microk8s kubectl exec -n price-tracker deployment/postgres -- psql -U admin -d price_tracker_db < database/test_schema.sql
```

## Indexes

The schema includes optimized indexes for common query patterns:

- `idx_listings_website`: Filter by website
- `idx_listings_scraped_at`: Time-based queries
- `idx_listings_brand`: Brand filtering
- `idx_listings_price`: Price range queries
- `idx_listings_url`: URL lookups
- `idx_searches_website`: Search term filtering
- `idx_searches_active`: Active search queries

## Future Considerations

1. **Partitioning**: Consider partitioning `listings` by date for large datasets
2. **Archiving**: Implement archiving strategy for old data
3. **Analytics**: Add materialized views for common price analysis queries
4. **Search Integration**: Consider full-text search indexes for listing names 