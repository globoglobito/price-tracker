# Database Schema Documentation

## Overview

This directory contains the database schema and migrations for the Price Tracker application. The schema is designed to be **comprehensive and flexible**, supporting both data-rich sites (eBay, Reverb) and data-poor sites (simple shops) with a single unified structure.

## Schema Design

### Core Philosophy

- **Comprehensive Data Structure**: Single table handles all websites with rich optional fields
- **Maximum Flexibility**: No restrictive constraints - supports any website, condition, or currency
- **Append-Only Strategy**: Each scrape creates new records for historical price tracking
- **Scalable Design**: Supports pod-per-search-term architecture
- **Future-Proof**: Ready for any new website without schema changes

### Tables

#### `searches` Table
Stores user-defined search terms for different websites.

```sql
CREATE TABLE price_tracker.searches (
    id SERIAL PRIMARY KEY,
    search_term VARCHAR(255) NOT NULL,
    website VARCHAR(50) NOT NULL DEFAULT 'ebay',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP,
    scrape_frequency_hours INTEGER DEFAULT 24,
    UNIQUE(search_term, website)
);
```

**Fields:**
- `search_term`: The search query (e.g., "Selmer Mark VI")
- `website`: Target website (e.g., "ebay", "reverb", "shopgoodwill")
- `is_active`: Whether this search should continue running
- `last_scraped_at`: Last time this search was scraped
- `scrape_frequency_hours`: How often to scrape (default: 24 hours)
- `created_at/updated_at`: Timestamps for tracking

#### `listings` Table
Stores scraped listings with comprehensive data structure supporting any website.

```sql
CREATE TABLE price_tracker.listings (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES price_tracker.searches(id) ON DELETE CASCADE,
    
    -- Basic listing information (always available)
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    website VARCHAR(50) NOT NULL DEFAULT 'ebay',
    listing_id VARCHAR(100), -- External listing ID from the website
    
    -- Pricing information
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    original_price DECIMAL(10,2), -- Original/retail price if available
    shipping_cost DECIMAL(10,2),
    
    -- Item details
    brand VARCHAR(100),
    model VARCHAR(100),
    type VARCHAR(100),
    condition VARCHAR(50), -- Used, New, Open box, For parts or not working, etc.
    
    -- Location and shipping
    seller_location VARCHAR(100),
    shipping_info TEXT,
    
    -- Auction/sale specific fields
    has_best_offer BOOLEAN DEFAULT FALSE,
    auction_end_time TIMESTAMP,
    sold_quantity INTEGER,
    
    -- Timestamps
    date_listed TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- Ensure unique listings per website
    UNIQUE(website, listing_id)
);
```

**Required Fields (always populated):**
- `title`: Title/name of the listing
- `price`: Current listing price
- `url`: Direct link to listing
- `website`: Source website
- `scraped_at`: When data was scraped

**Optional Fields (site-dependent, can be NULL):**
- `brand`: Item brand (e.g., "Yamaha", "Selmer")
- `model`: Specific model (e.g., "Mark VI", "YTS-61")
- `type`: Saxophone type (e.g., "Tenor", "Alto")
- `condition`: Item condition (e.g., "Used", "New", "For parts or not working")
- `seller_location`: Seller's location (country/region)
- `shipping_info`: Shipping details and options
- `currency`: Price currency (USD, EUR, PEN, etc.)
- `original_price`: Original/retail price if available
- `shipping_cost`: Shipping cost if available
- `has_best_offer`: Whether listing accepts best offers
- `auction_end_time`: For auction listings
- `sold_quantity`: For multi-quantity listings
- `date_listed`: When item was originally listed
- `is_active`: Whether the listing is currently active
- `first_seen_at` / `last_seen_at`: Lifecycle tracking for incremental scrapes
- `ended_at`: When the listing was marked inactive

## Usage Examples

### Data-Rich Site (eBay)
```sql
INSERT INTO price_tracker.listings (
    title, price, url, website, scraped_at,
    brand, model, type, condition, seller_location,
    currency, shipping_cost, has_best_offer
) VALUES (
    'YAMAHA YTS-61S Tenor Saxophone - Excellent Condition', 2400.00,
    'https://www.ebay.com/itm/357413100867', 'ebay', NOW(),
    'Yamaha', 'YTS-61S', 'Tenor', 'Used', 'Fukuoka Ken, Japan',
    'USD', 25.00, true
);
```

### Data-Poor Site (Simple Shop)
```sql
INSERT INTO price_tracker.listings (
    title, price, url, website, scraped_at
) VALUES (
    'Saxophone for Sale', 500.00,
    'https://example-shop.com/saxophone-123', 'example-shop', NOW()
);
```

### International Site (Different Currency)
```sql
INSERT INTO price_tracker.listings (
    title, price, url, website, scraped_at,
    brand, model, condition, seller_location, currency
) VALUES (
    'Selmer Mark VI Tenor Saxophone', 3500.00,
    'https://mercado-libre.com/selmer-mark-vi', 'mercadolibre', NOW(),
    'Selmer', 'Mark VI', 'Used', 'Buenos Aires, Argentina', 'ARS'
);
```

## Migration Management

### Current Migration
- **`001_complete_schema.sql`**: Comprehensive schema with all fields for any website

### Applying Migrations
```bash
# Apply the complete schema
./database/apply_migration.sh database/migrations/001_complete_schema.sql
```

## Performance Optimization

### Indexes
The schema includes comprehensive indexing for optimal query performance:

- **Website-based queries**: `idx_listings_website`
- **Time-based queries**: `idx_listings_scraped_at`
- **Brand/model searches**: `idx_listings_brand`
- **Price filtering**: `idx_listings_price`
- **Condition filtering**: `idx_listings_condition`
- **Location queries**: `idx_listings_seller_location`
- **Currency filtering**: `idx_listings_currency`
- **Auction queries**: `idx_listings_auction_end_time`
- **Combined queries**: `idx_listings_condition_price`
- **Search relationships**: `idx_listings_search_id`

### Testing
```bash
# Run comprehensive database tests
./database/test_integration.sh
```

Tests verify:
- ✅ Schema creation and isolation
- ✅ Table structure and constraints
- ✅ Index creation and usage
- ✅ Data insertion (rich and minimal)
- ✅ Data retrieval and querying
- ✅ Data type validation
- ✅ Cleanup operations

## Flexibility Features

### Website Support
The schema supports **any website** without constraints:
- **eBay**: Rich data with condition, shipping, auctions
- **Reverb**: Similar rich data structure
- **ShopGoodwill**: Basic data
- **Facebook Marketplace**: Social commerce data
- **Craigslist**: Local classified data
- **International sites**: Any currency, any language
- **Future sites**: No schema changes needed

### Data Validation
- **No restrictive constraints**: Maximum flexibility
- **Application-level validation**: Handle data quality in scrapers
- **NULL-friendly**: Missing data doesn't break queries
- **Type safety**: Proper data types for each field

### Scalability
- **Pod-per-search**: Each search term runs in isolated pod
- **Historical tracking**: All scrapes preserved
- **Efficient queries**: Optimized indexes for common patterns
- **Future-ready**: Schema supports any new requirements 