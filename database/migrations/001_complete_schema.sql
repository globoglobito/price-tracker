-- Migration: 001_complete_schema.sql
-- Description: Complete database schema for Price Tracker supporting eBay and future sites
-- Date: 2024-12-19

-- Create dedicated schema for price tracker
CREATE SCHEMA IF NOT EXISTS price_tracker;
SET search_path TO price_tracker, public;

-- Table: searches - User-defined search terms
CREATE TABLE IF NOT EXISTS price_tracker.searches (
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

-- Table: listings - Scraped listing data from various websites
CREATE TABLE IF NOT EXISTS price_tracker.listings (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES price_tracker.searches(id) ON DELETE CASCADE,
    
    -- Basic listing information
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    website VARCHAR(50) NOT NULL DEFAULT 'ebay',
    listing_id VARCHAR(100), -- External listing ID from the website
    
    -- Pricing information
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    original_price DECIMAL(10,2), -- Original/retail price if available
    -- shipping_cost dropped (prefer shipping_info text; amounts parsed when needed)
    
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
    -- watchers_count/sold_quantity/available_quantity dropped for simplicity
    
    -- Timestamps
    -- date_listed dropped
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    notes TEXT,
    
    -- Ensure unique listings per website
    UNIQUE(website, listing_id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_listings_website ON price_tracker.listings(website);
CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON price_tracker.listings(scraped_at);
CREATE INDEX IF NOT EXISTS idx_listings_brand ON price_tracker.listings(brand);
CREATE INDEX IF NOT EXISTS idx_listings_price ON price_tracker.listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_url ON price_tracker.listings(url);
CREATE INDEX IF NOT EXISTS idx_listings_condition ON price_tracker.listings(condition);
CREATE INDEX IF NOT EXISTS idx_listings_seller_location ON price_tracker.listings(seller_location);
CREATE INDEX IF NOT EXISTS idx_listings_currency ON price_tracker.listings(currency);
CREATE INDEX IF NOT EXISTS idx_listings_auction_end_time ON price_tracker.listings(auction_end_time);
CREATE INDEX IF NOT EXISTS idx_listings_condition_price ON price_tracker.listings(condition, price);
CREATE INDEX IF NOT EXISTS idx_listings_search_id ON price_tracker.listings(search_id);

-- Indexes for searches table
CREATE INDEX IF NOT EXISTS idx_searches_website ON price_tracker.searches(website);
CREATE INDEX IF NOT EXISTS idx_searches_active ON price_tracker.searches(is_active);
CREATE INDEX IF NOT EXISTS idx_searches_term ON price_tracker.searches(search_term);

-- Add comments for documentation
COMMENT ON SCHEMA price_tracker IS 'Schema for Price Tracker application - tracks saxophone prices across multiple websites';
COMMENT ON TABLE price_tracker.searches IS 'User-defined search terms for different websites';
COMMENT ON TABLE price_tracker.listings IS 'Scraped listing data from various websites (eBay, Reverb, etc.) with comprehensive fields for rich data';

COMMENT ON COLUMN price_tracker.searches.search_term IS 'The search term to look for (e.g., "Selmer Mark VI")';
COMMENT ON COLUMN price_tracker.searches.website IS 'Target website for scraping (ebay, reverb, etc.)';
COMMENT ON COLUMN price_tracker.searches.is_active IS 'Whether this search should be actively monitored';
COMMENT ON COLUMN price_tracker.searches.last_scraped_at IS 'Last time this search was scraped';
COMMENT ON COLUMN price_tracker.searches.scrape_frequency_hours IS 'How often to scrape this search term';

COMMENT ON COLUMN price_tracker.listings.title IS 'Listing title/name';
COMMENT ON COLUMN price_tracker.listings.url IS 'Direct URL to the listing';
COMMENT ON COLUMN price_tracker.listings.website IS 'Source website (ebay, reverb, etc.)';
COMMENT ON COLUMN price_tracker.listings.listing_id IS 'External listing ID from the website';
COMMENT ON COLUMN price_tracker.listings.price IS 'Current listing price';
COMMENT ON COLUMN price_tracker.listings.currency IS 'Price currency (USD, EUR, PEN, etc.)';
COMMENT ON COLUMN price_tracker.listings.original_price IS 'Original/retail price if available';
-- shipping_cost comment removed
COMMENT ON COLUMN price_tracker.listings.brand IS 'Item brand (e.g., Selmer, Yamaha)';
COMMENT ON COLUMN price_tracker.listings.model IS 'Item model (e.g., Mark VI, YAS-62)';
COMMENT ON COLUMN price_tracker.listings.type IS 'Item type (e.g., Alto Sax, Tenor Sax)';
COMMENT ON COLUMN price_tracker.listings.condition IS 'Item condition: Used, New, Open box, For parts or not working, etc.';
COMMENT ON COLUMN price_tracker.listings.seller_location IS 'Seller location (country/region)';
COMMENT ON COLUMN price_tracker.listings.shipping_info IS 'Shipping details and options';
COMMENT ON COLUMN price_tracker.listings.has_best_offer IS 'Whether the listing accepts best offers';
COMMENT ON COLUMN price_tracker.listings.auction_end_time IS 'Auction end time for auction listings';
-- removed comments for dropped columns
COMMENT ON COLUMN price_tracker.listings.scraped_at IS 'When this data was scraped';
COMMENT ON COLUMN price_tracker.listings.notes IS 'Additional notes or metadata';

-- No restrictive constraints - maximum flexibility for any website, condition, or currency


