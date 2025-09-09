#!/usr/bin/env python3
"""
eBay Collector - Scrapes search results and queues listings for enrichment.

This component:
1. Scrapes eBay search results pages 
2. Extracts basic listing data (title, price, URL, etc.)
3. Upserts basic listings to database immediately
4. Publishes individual listings to RabbitMQ for parallel enrichment
"""
import logging
import os
import sys
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.playwright_ebay_scraper import EbayBrowserScraper
from scraper.config import settings
from scraper.utils.queue_manager import QueueManager, get_queue_manager_from_env
from scraper.db import upsert_listings, get_or_create_search

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EbayCollector:
    """Collects eBay search results and queues listings for enrichment."""
    
    def __init__(self):
        """Initialize the collector."""
        self.search_term = settings.get_search_term()
        self.max_pages = settings.get_max_pages()
        self.headless = settings.is_headless()
        self.browser_name = settings.get_browser_type()
        # Use unique profile directory per collector to avoid conflicts
        base_user_data_dir = settings.get_user_data_dir()
        if base_user_data_dir:
            import os
            worker_id = os.environ.get('HOSTNAME', 'collector')
            self.user_data_dir = f"{base_user_data_dir}/{worker_id}"
        else:
            self.user_data_dir = None
        self.slow_mo_ms = settings.get_slow_mo_ms()
        self.debug_snapshot_dir = settings.get_debug_snapshot_dir()
        self.timeout_ms = settings.get_timeout_ms()
        
        # Initialize scraper for search results only (no enrichment)
        self.scraper = EbayBrowserScraper(
            search_term=self.search_term,
            max_pages=self.max_pages,
            delay_seconds=2.5,
            headless=self.headless,
            browser_name=self.browser_name,
            user_data_dir=self.user_data_dir,
            slow_mo_ms=self.slow_mo_ms,
            debug_snapshot_dir=self.debug_snapshot_dir,
            timeout_ms=self.timeout_ms,
            enrich_limit=0,  # No enrichment in collector
            snapshot_dir=None  # No snapshots in collector
        )
        
        # Initialize queue manager
        try:
            self.queue_manager = get_queue_manager_from_env()
        except ImportError as e:
            logger.error(f"Queue manager initialization failed: {e}")
            sys.exit(1)
    
    def collect_and_queue_listings(self) -> Dict[str, int]:
        """
        Collect search results and queue listings for enrichment.
        
        Returns:
            Dictionary with collection statistics
        """
        logger.info(f"Starting collection for search term: '{self.search_term}'")
        
        stats = {
            'pages_scraped': 0,
            'listings_found': 0,
            'listings_upserted': 0,
            'listings_queued': 0,
            'errors': 0
        }
        
        try:
            # Connect to queue
            self.queue_manager.connect()
            
            # Scrape search results (no enrichment)
            logger.info("Scraping search results...")
            listings = self.scraper.scrape()
            
            stats['listings_found'] = len(listings)
            logger.info(f"Found {len(listings)} listings")
            
            if not listings:
                logger.warning("No listings found")
                return stats
            
            # Upsert basic listings to database
            try:
                search_id = get_or_create_search(self.search_term, "ebay")
                
                # Add search_id to all listings
                for listing in listings:
                    listing['search_id'] = search_id
                    
                upserted_count = upsert_listings(listings)
                stats['listings_upserted'] = upserted_count
                logger.info(f"Upserted {upserted_count} basic listings to database")
                
            except Exception as e:
                logger.error(f"Failed to upsert listings to database: {e}")
                stats['errors'] += 1
                # Continue with queueing even if DB upsert fails
            
            # Queue individual listings for enrichment
            logger.info("Queueing listings for enrichment...")
            queued_count = self.queue_manager.publish_batch_for_enrichment(listings)
            stats['listings_queued'] = queued_count
            
            if queued_count != len(listings):
                logger.warning(f"Only queued {queued_count}/{len(listings)} listings")
                stats['errors'] += (len(listings) - queued_count)
            
            # Get queue statistics
            queue_stats = self.queue_manager.get_queue_stats()
            logger.info(f"Queue stats: {queue_stats}")
            
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            stats['errors'] += 1
            raise
            
        finally:
            # Cleanup
            try:
                self.queue_manager.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect from queue: {e}")
            
            self._cleanup_profile()
        
        return stats
    
    def _cleanup_profile(self):
        """Clean up the unique profile directory created for this collector."""
        if self.user_data_dir:
            try:
                import shutil
                import os
                if os.path.exists(self.user_data_dir):
                    shutil.rmtree(self.user_data_dir)
                    logger.info(f"Cleaned up profile directory: {self.user_data_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup profile directory {self.user_data_dir}: {e}")
    
    def run(self) -> None:
        """Run the collector."""
        try:
            stats = self.collect_and_queue_listings()
            
            logger.info("Collection completed successfully!")
            logger.info(f"Collection stats: {stats}")
            
            if stats['errors'] > 0:
                logger.warning(f"Collection completed with {stats['errors']} errors")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            sys.exit(1)


def main():
    """Main entry point for the collector."""
    logger.info("Starting eBay Collector")
    
    collector = EbayCollector()
    collector.run()


if __name__ == "__main__":
    main()
