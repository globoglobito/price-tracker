#!/usr/bin/env python3
"""
eBay Worker - Processes individual listings from queue with enrichment.

This component:
1. Consumes listings from RabbitMQ queue
2. Enriches each listing with detailed data (one at a time)
3. Immediately upserts enriched data to database
4. Acknowledges successful processing to queue
"""
import json
import logging
import os
import sys
import signal
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pika
from scraper.extractors.listing_enricher import ListingEnricher
from scraper.utils.queue_manager import QueueManager, get_queue_manager_from_env
from scraper.config import settings
from scraper.db import upsert_listings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EbayWorker:
    """Processes individual listings from queue with enrichment."""
    
    def __init__(self):
        """Initialize the worker."""
        self.running = True
        self.processed_count = 0
        self.failed_count = 0
        
        # Get configuration
        self.snapshot_dir = settings.get_snapshot_dir()
        self.debug_snapshot_dir = settings.get_debug_snapshot_dir()
        self.timeout_ms = settings.get_timeout_ms()
        
        # Initialize listing enricher
        self.enricher = ListingEnricher(
            snapshot_dir=self.snapshot_dir,
            debug_snapshot_dir=self.debug_snapshot_dir,
            timeout_ms=self.timeout_ms,
            screenshot_timeout_ms=int(os.environ.get("SCREENSHOT_TIMEOUT_MS", "10000")),
            content_timeout_ms=int(os.environ.get("CONTENT_TIMEOUT_MS", "5000"))
        )
        
        # Initialize queue manager
        try:
            self.queue_manager = get_queue_manager_from_env()
        except ImportError as e:
            logger.error(f"Queue manager initialization failed: {e}")
            sys.exit(1)
            
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def process_listing(self, ch, method, properties, body) -> None:
        """
        Process a single listing from the queue.
        
        Args:
            ch: Channel
            method: Method
            properties: Properties  
            body: Message body (JSON listing data)
        """
        try:
            # Parse listing data
            listing_data = json.loads(body.decode('utf-8'))
            listing_id = listing_data.get('listing_id', 'unknown')
            
            logger.info(f"Processing listing: {listing_id}")
            
            # Create a browser context for this listing
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as playwright:
                # Launch browser
                browser_type = getattr(playwright, settings.get_browser_type())
                
                launch_kwargs = {
                    "headless": settings.is_headless(),
                    "slow_mo": settings.get_slow_mo_ms()
                }
                
                browser = browser_type.launch(**launch_kwargs)
                
                try:
                    # Create context and page
                    context = browser.new_context()
                    page = context.new_page()
                    
                    # Navigate to listing URL
                    url = listing_data.get('url')
                    if not url:
                        raise ValueError("No URL provided for listing")
                    
                    logger.debug(f"Navigating to: {url}")
                    page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    
                    # Extract detailed listing data directly with timeout handling
                    try:
                        # Set a page timeout for the extraction
                        page.set_default_timeout(self.timeout_ms)
                        self.enricher.extract_listing_data(page, listing_data, 1, 1)
                    except Exception as extract_error:
                        logger.warning(f"Extraction failed for listing {listing_id}: {extract_error}")
                        # Continue with basic data - don't fail the whole process
                        pass
                    
                    # Immediately upsert enriched data to database
                    try:
                        upserted_count = upsert_listings([listing_data])
                        logger.info(f"Successfully enriched and upserted listing {listing_id} (count: {upserted_count})")
                        
                    except Exception as db_error:
                        logger.error(f"Failed to upsert enriched listing {listing_id}: {db_error}")
                        # Don't raise - we'll still ACK the message to avoid reprocessing
                        # The basic listing data was already saved by the collector
                    
                    # Acknowledge successful processing
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self.processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to enrich listing {listing_id}: {e}")
                    
                    # Check if this is a permanent failure (e.g., bad URL, missing page)
                    error_str = str(e).lower()
                    if any(term in error_str for term in ['404', 'not found', 'invalid url', 'timeout']):
                        # Permanent failure - ACK to remove from queue
                        logger.warning(f"Permanent failure for listing {listing_id}, acknowledging to remove from queue")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        # Temporary failure - NACK to requeue
                        logger.warning(f"Temporary failure for listing {listing_id}, requeuing for retry")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                        
                    self.failed_count += 1
                    
                finally:
                    # Cleanup browser resources
                    try:
                        context.close()
                    except Exception:
                        pass
                    
                    try:
                        browser.close()
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.error(f"Critical error processing message: {e}")
            # NACK message to requeue for retry
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            except Exception:
                pass
            self.failed_count += 1
    
    def run(self) -> None:
        """Run the worker to process listings from queue."""
        logger.info("Starting eBay Worker")
        
        try:
            # Connect to queue
            self.queue_manager.connect()
            
            logger.info("Worker ready, waiting for listings...")
            
            # Start consuming from queue
            self.queue_manager.consume_listing_for_enrichment(
                callback_func=self.process_listing,
                auto_ack=False  # Manual ACK for better error handling
            )
            
        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker failed: {e}")
            sys.exit(1)
        finally:
            # Cleanup
            try:
                self.queue_manager.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect from queue: {e}")
            
            logger.info(f"Worker shutdown complete. Processed: {self.processed_count}, Failed: {self.failed_count}")


def main():
    """Main entry point for the worker."""
    worker = EbayWorker()
    worker.run()


if __name__ == "__main__":
    main()
