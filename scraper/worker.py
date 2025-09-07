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
        self.user_data_dir = None  # Track for cleanup
        
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
                # Use same sophisticated browser setup as monolithic scraper
                browser_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]

                launch_kwargs = {
                    "headless": settings.is_headless(),
                    "args": browser_args,
                }
                
                # Prefer Chromium's newer headless mode for closer fingerprint
                if settings.is_headless() and settings.get_browser_type() == "chromium":
                    try:
                        if "--headless=new" not in launch_kwargs["args"]:
                            launch_kwargs["args"].append("--headless=new")
                    except Exception:
                        pass

                browser_type = getattr(playwright, settings.get_browser_type())
                context = None
                browser = None
                
                try:
                    # Persistent context if user data dir provided (like monolithic)
                    # Use unique profile directory per worker to avoid conflicts
                    base_user_data_dir = settings.get_user_data_dir()
                    if base_user_data_dir and settings.get_browser_type() in ("chromium", "firefox"):
                        import os
                        worker_id = os.environ.get('HOSTNAME', 'worker')
                        user_data_dir = f"{base_user_data_dir}-{worker_id}"
                        self.user_data_dir = user_data_dir  # Track for cleanup
                        
                        # Pre-create the directory with proper permissions before Chromium uses it
                        os.makedirs(user_data_dir, mode=0o777, exist_ok=True)
                        
                        persist_kwargs = dict(launch_kwargs)
                        if settings.get_slow_mo_ms():
                            persist_kwargs["slow_mo"] = settings.get_slow_mo_ms()
                        context = browser_type.launch_persistent_context(user_data_dir, **persist_kwargs)
                        page = context.new_page()
                    else:
                        # Regular browser launch with sophisticated setup
                        if settings.get_slow_mo_ms():
                            launch_kwargs["slow_mo"] = settings.get_slow_mo_ms()
                        browser = browser_type.launch(**launch_kwargs)
                        context = browser.new_context()
                        page = context.new_page()
                    
                    # Use the proper enrichment method like the monolithic scraper
                    # enrich_and_snapshot handles navigation, retries, and timeouts properly
                    self.enricher.enrich_and_snapshot(page, [listing_data], 1)
                    
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
                    # Cleanup browser resources (same as monolithic)
                    try:
                        if context:
                            context.close()
                    except Exception:
                        pass
                    
                    try:
                        if browser:
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
            
            self._cleanup_profile()
            logger.info(f"Worker shutdown complete. Processed: {self.processed_count}, Failed: {self.failed_count}")
    
    def _cleanup_profile(self):
        """Clean up the unique profile directory created for this worker."""
        if self.user_data_dir:
            try:
                import shutil
                import os
                if os.path.exists(self.user_data_dir):
                    shutil.rmtree(self.user_data_dir)
                    logger.info(f"Cleaned up profile directory: {self.user_data_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup profile directory {self.user_data_dir}: {e}")


def main():
    """Main entry point for the worker."""
    worker = EbayWorker()
    worker.run()


if __name__ == "__main__":
    main()
