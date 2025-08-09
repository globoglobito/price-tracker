#!/usr/bin/env python3
"""
eBay Scraper for Price Tracker
Scrapes eBay listings for saxophones and other musical instruments
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EbayScraper:
    """eBay scraper using requests and BeautifulSoup"""
    
    def __init__(self, search_term: str, max_pages: int = 3, delay: float = 2.0):
        """
        Initialize the eBay scraper
        
        Args:
            search_term: What to search for (e.g., "Selmer Mark VI")
            max_pages: Maximum number of pages to scrape
            delay: Delay between requests (seconds)
        """
        self.search_term = search_term
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        
        # Set up headers to look more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        logger.info(f"Initialized eBay scraper for: {search_term}")
    
    def _build_search_url(self, page: int = 1) -> str:
        """Build eBay search URL"""
        base_url = "https://www.ebay.com/sch/i.html"
        params = {
            '_nkw': self.search_term,
            '_pgn': page,
            '_sacat': 0,  # All categories
            'LH_TitleDesc': 0,  # Search title and description
            'LH_Sold': 0,  # Not sold items (active listings only)
        }
        
        # Build URL with parameters
        url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url
    
    def _extract_price(self, price_element) -> Optional[float]:
        """Extract price from price element"""
        if not price_element:
            return None
            
        price_text = price_element.get_text(strip=True)
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
        return None
    
    def _extract_condition(self, item) -> Optional[str]:
        """Extract item condition"""
        # Look for condition in various places
        condition_selectors = [
            '.s-item__condition',
            '.s-item__subtitle',
            '.s-item__title',
            '.s-item__details'
        ]
        
        for selector in condition_selectors:
            condition_elem = item.select_one(selector)
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True).lower()
                
                # Map common condition terms
                if 'used' in condition_text:
                    return 'Used'
                elif 'new' in condition_text:
                    return 'New'
                elif 'open box' in condition_text:
                    return 'Open box'
                elif 'for parts' in condition_text or 'not working' in condition_text:
                    return 'For parts or not working'
                elif 'refurbished' in condition_text:
                    return 'Certified - Refurbished'
        
        return 'Not Specified'
    
    def _extract_location(self, item) -> Optional[str]:
        """Extract seller location"""
        location_elem = item.select_one('.s-item__location')
        if location_elem:
            return location_elem.get_text(strip=True)
        return None
    
    def _extract_shipping_info(self, item) -> Optional[str]:
        """Extract shipping information"""
        shipping_elem = item.select_one('.s-item__shipping')
        if shipping_elem:
            return shipping_elem.get_text(strip=True)
        return None
    
    def _extract_listing_id(self, item) -> Optional[str]:
        """Extract eBay listing ID from URL"""
        link_elem = item.select_one('.s-item__link')
        if link_elem:
            url = link_elem.get('href', '')
            # Extract ID from URL like /itm/123456789
            match = re.search(r'/itm/(\d+)', url)
            if match:
                return match.group(1)
        return None
    
    def _parse_listing_item(self, item) -> Optional[Dict]:
        """Parse a single listing item"""
        try:
            # Extract basic info
            title_elem = item.select_one('.s-item__title')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if title == "Shop on eBay":  # Skip sponsored items
                return None
            
            # Extract URL
            link_elem = item.select_one('.s-item__link')
            url = link_elem.get('href') if link_elem else None
            
            # Extract price
            price_elem = item.select_one('.s-item__price')
            price = self._extract_price(price_elem)
            
            if not price:  # Skip items without price
                return None
            
            # Extract additional info
            condition = self._extract_condition(item)
            location = self._extract_location(item)
            shipping_info = self._extract_shipping_info(item)
            listing_id = self._extract_listing_id(item)
            
            # Extract brand/model from title (basic parsing)
            brand = None
            model = None
            type_info = None
            
            title_lower = title.lower()
            if 'selmer' in title_lower:
                brand = 'Selmer'
                if 'mark vi' in title_lower:
                    model = 'Mark VI'
            elif 'yamaha' in title_lower:
                brand = 'Yamaha'
                # Extract model patterns like YTS-61, YAS-62, etc.
                model_match = re.search(r'Y[AT]S?[-\s]?(\d+)', title, re.IGNORECASE)
                if model_match:
                    model = f"YTS-{model_match.group(1)}"
            
            # Determine saxophone type
            if 'tenor' in title_lower:
                type_info = 'Tenor'
            elif 'alto' in title_lower:
                type_info = 'Alto'
            elif 'soprano' in title_lower:
                type_info = 'Soprano'
            elif 'baritone' in title_lower:
                type_info = 'Baritone'
            
            return {
                'title': title,
                'price': price,
                'url': url,
                'listing_id': listing_id,
                'condition': condition,
                'seller_location': location,
                'shipping_info': shipping_info,
                'brand': brand,
                'model': model,
                'type': type_info,
                'currency': 'USD',  # Default for eBay US
                'website': 'ebay',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error parsing listing item: {e}")
            return None
    
    def scrape_page(self, page: int) -> List[Dict]:
        """Scrape a single page of eBay search results"""
        url = self._build_search_url(page)
        logger.info(f"Scraping page {page}: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got a bot detection page
            if "results for" not in response.text.lower():
                logger.warning(f"Page {page} might be a bot detection page - no 'results for' found")
                logger.warning(f"Response length: {len(response.text)} characters")
                return []
            
            # Find all listing items
            items = soup.select('.s-item')
            logger.info(f"Found {len(items)} items on page {page}")
            
            if len(items) < 10:  # Suspiciously few items
                logger.warning(f"Page {page} has very few items ({len(items)}) - might be blocked")
                return []
            
            listings = []
            for item in items:
                listing = self._parse_listing_item(item)
                if listing:
                    listings.append(listing)
            
            logger.info(f"Successfully parsed {len(listings)} listings from page {page}")
            return listings
            
        except requests.RequestException as e:
            logger.error(f"Error scraping page {page}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping page {page}: {e}")
            return []
    
    def scrape(self) -> List[Dict]:
        """Scrape multiple pages of eBay search results"""
        all_listings = []
        
        for page in range(1, self.max_pages + 1):
            listings = self.scrape_page(page)
            all_listings.extend(listings)
            
            # Add delay between requests
            if page < self.max_pages:
                delay = self.delay + random.uniform(0, 1)  # Add some randomness
                logger.info(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
        
        logger.info(f"Scraping complete. Total listings found: {len(all_listings)}")
        return all_listings


def main():
    """Test the scraper"""
    # Test with a saxophone search
    scraper = EbayScraper("Selmer Mark VI", max_pages=2, delay=3.0)
    listings = scraper.scrape()
    
    print(f"\nFound {len(listings)} listings:")
    for i, listing in enumerate(listings[:5], 1):  # Show first 5
        print(f"\n{i}. {listing['title']}")
        print(f"   Price: ${listing['price']}")
        print(f"   Condition: {listing['condition']}")
        print(f"   Location: {listing['seller_location']}")
        print(f"   URL: {listing['url']}")


if __name__ == "__main__":
    main()
