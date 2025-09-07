#!/usr/bin/env python3
"""
Test script for eBay scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.playwright_ebay_scraper import EbayBrowserScraper
import json


def test_scraper():
    """Test the eBay scraper with a simple search"""
    print("🧪 Testing eBay Scraper")
    print("=" * 50)
    
    # Test with a simple saxophone search
    search_term = "Selmer Mark VI"
    print(f"Searching for: {search_term}")
    
    try:
        # Initialize scraper with conservative settings
        scraper = EbayBrowserScraper(
            search_term=search_term,
            max_pages=3,  # Test 3 pages to get more results
            delay_seconds=3.0     # 3 second delay
        )
        
        # Run the scraper
        print("Starting scrape...")
        listings = scraper.scrape()
        
        print(f"\n✅ Scraping complete!")
        print(f"📊 Found {len(listings)} listings")
        
        if listings:
            print(f"\n📋 Sample listings:")
            for i, listing in enumerate(listings[:3], 1):  # Show first 3
                print(f"\n{i}. {listing['title']}")
                print(f"   💰 Price: ${listing['price']}")
                print(f"   📍 Location: {listing['seller_location']}")
                print(f"   🏷️  Condition: {listing['condition']}")
                print(f"   🏷️  Brand: {listing['brand']}")
                print(f"   🏷️  Model: {listing['model']}")
                print(f"   🏷️  Type: {listing['type']}")
                print(f"   🔗 URL: {listing['url']}")
            
            # Save sample to JSON for inspection
            sample_file = "sample_listings.json"
            with open(sample_file, 'w') as f:
                json.dump(listings[:5], f, indent=2)
            print(f"\n💾 Saved sample data to: {sample_file}")
            
        else:
            print("❌ No listings found")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\n🎉 Scraper test completed successfully!")
    else:
        print("\n💥 Scraper test failed!")
        sys.exit(1)
