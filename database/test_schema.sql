-- Test script to verify database schema
-- Run this after applying the migration to test the tables

-- Set search path to use the price_tracker schema
SET search_path TO price_tracker, public;

-- Test 1: Insert a sample search term
INSERT INTO price_tracker.searches (search_term, website) 
VALUES ('Selmer Mark VI', 'ebay') 
ON CONFLICT (search_term, website) DO NOTHING;

-- Test 2: Insert sample listings with different data richness levels

-- Rich data listing (like eBay)
INSERT INTO price_tracker.listings (
    listing_name, 
    price, 
    url, 
    website, 
    scraped_at,
    brand,
    model,
    type,
    date_listed,
    location
) VALUES (
    'YAMAHA YTS-61S Tenor Saxophone',
    2400.00,
    'https://www.ebay.com/itm/357413100867',
    'ebay',
    CURRENT_TIMESTAMP,
    'Yamaha',
    'YTS-61S',
    'Tenor',
    CURRENT_DATE - INTERVAL '5 days',
    'Fukuoka Ken, Japan'
);

-- Minimal data listing (like a simple shop)
INSERT INTO price_tracker.listings (
    listing_name, 
    price, 
    url, 
    website, 
    scraped_at
) VALUES (
    'Saxophone for Sale',
    500.00,
    'https://example-shop.com/saxophone-123',
    'example-shop',
    CURRENT_TIMESTAMP
);

-- Medium data listing
INSERT INTO price_tracker.listings (
    listing_name, 
    price, 
    url, 
    website, 
    scraped_at,
    brand,
    type,
    location
) VALUES (
    'Vintage Conn Tenor Saxophone',
    1199.00,
    'https://www.ebay.com/itm/example-conn',
    'ebay',
    CURRENT_TIMESTAMP,
    'Conn',
    'Tenor',
    'Santa Fe, New Mexico'
);

-- Test 3: Query to verify data
SELECT '=== SEARCHES TABLE ===' as info;
SELECT * FROM price_tracker.searches;

SELECT '=== LISTINGS TABLE ===' as info;
SELECT 
    listing_name,
    price,
    website,
    brand,
    model,
    type,
    location,
    scraped_at
FROM price_tracker.listings 
ORDER BY scraped_at DESC;

-- Test 4: Verify indexes
SELECT '=== INDEXES ===' as info;
SELECT 
    indexname,
    tablename
FROM pg_indexes 
WHERE tablename IN ('searches', 'listings') AND schemaname = 'price_tracker'
ORDER BY tablename, indexname; 