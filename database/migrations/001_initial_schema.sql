-- Initial Database Schema for Price Tracker
-- Migration: 001_initial_schema.sql
-- Description: Creates the core tables for searches and listings

-- Create dedicated schema for price tracker
CREATE SCHEMA IF NOT EXISTS price_tracker;

-- Set search path to use the new schema
SET search_path TO price_tracker, public;

-- Create searches table to store user-defined search terms
CREATE TABLE IF NOT EXISTS price_tracker.searches (
    id SERIAL PRIMARY KEY,
    search_term VARCHAR(200) NOT NULL,
    website VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique search term per website
    UNIQUE(search_term, website)
);

-- Create listings table to store scraped listings
CREATE TABLE IF NOT EXISTS price_tracker.listings (
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
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_listings_website ON price_tracker.listings(website);
CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON price_tracker.listings(scraped_at);
CREATE INDEX IF NOT EXISTS idx_listings_brand ON price_tracker.listings(brand);
CREATE INDEX IF NOT EXISTS idx_listings_price ON price_tracker.listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_url ON price_tracker.listings(url);

-- Create index for searches
CREATE INDEX IF NOT EXISTS idx_searches_website ON price_tracker.searches(website);
CREATE INDEX IF NOT EXISTS idx_searches_active ON price_tracker.searches(is_active);

-- Add comments for documentation
COMMENT ON TABLE price_tracker.searches IS 'User-defined search terms for different websites';
COMMENT ON TABLE price_tracker.listings IS 'Scraped listings from various websites with flexible data structure';
COMMENT ON COLUMN price_tracker.listings.listing_name IS 'Title/name of the listing (required)';
COMMENT ON COLUMN price_tracker.listings.price IS 'Current price of the item (required)';
COMMENT ON COLUMN price_tracker.listings.url IS 'Direct link to the listing (required)';
COMMENT ON COLUMN price_tracker.listings.website IS 'Source website (eBay, Reverb, etc.) (required)';
COMMENT ON COLUMN price_tracker.listings.scraped_at IS 'When this data was scraped (required)';
COMMENT ON COLUMN price_tracker.listings.brand IS 'Brand of the item (optional, site-dependent)';
COMMENT ON COLUMN price_tracker.listings.model IS 'Model of the item (optional, site-dependent)';
COMMENT ON COLUMN price_tracker.listings.type IS 'Type of saxophone (optional, site-dependent)';
COMMENT ON COLUMN price_tracker.listings.date_listed IS 'When the listing was created (optional, site-dependent)';
COMMENT ON COLUMN price_tracker.listings.location IS 'Location of the item (optional, site-dependent)'; 