"""
Tests for worker module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.worker import EbayWorker


class TestEbayWorker:
    """Test cases for EbayWorker class."""

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_worker_initialization(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test worker initializes correctly with proper configuration."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = "/tmp/test"
        mock_settings.get_slow_mo_ms.return_value = 100
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher.return_value = Mock()
        
        # Create worker
        worker = EbayWorker()
        
        # Verify initialization
        assert worker.running is True
        assert worker.processed_count == 0
        assert worker.failed_count == 0
        assert worker.user_data_dir is None  # Initially None
        assert worker.snapshot_dir == "/tmp/snapshots"
        assert worker.debug_snapshot_dir == "/tmp/debug"
        assert worker.timeout_ms == 30000
        
        # Verify enricher was initialized correctly
        mock_enricher.assert_called_once()
        call_args = mock_enricher.call_args
        assert call_args[1]['snapshot_dir'] == "/tmp/snapshots"
        assert call_args[1]['debug_snapshot_dir'] == "/tmp/debug"
        assert call_args[1]['timeout_ms'] == 30000

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_signal_handler(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test signal handler sets running to False."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher.return_value = Mock()
        
        # Create worker
        worker = EbayWorker()
        
        # Test signal handler
        assert worker.running is True
        worker._signal_handler(2, None)  # SIGINT
        assert worker.running is False

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    @patch('scraper.worker.upsert_listings')
    def test_process_listing_success(self, mock_upsert, mock_queue_manager, mock_enricher, mock_settings):
        """Test successful processing of a listing."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher_instance = Mock()
        mock_enricher.return_value = mock_enricher_instance
        
        # Mock database operations
        mock_upsert.return_value = 1
        
        # Create worker
        worker = EbayWorker()
        
        # Mock channel and method
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        # Test listing data
        listing_data = {
            "listing_id": "12345",
            "title": "Test Item",
            "price": 100.0,
            "url": "https://example.com/item"
        }
        mock_body = json.dumps(listing_data).encode('utf-8')
        
        # Mock Playwright context
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
            
            mock_browser_type = Mock()
            mock_playwright_instance.chromium = mock_browser_type
            
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()
            
            mock_browser_type.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # Process listing
            worker.process_listing(mock_channel, mock_method, None, mock_body)
            
            # Verify results
            assert worker.processed_count == 1
            assert worker.failed_count == 0
            
            # Verify method calls
            mock_enricher_instance.enrich_and_snapshot.assert_called_once()
            mock_upsert.assert_called_once()
            mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_process_listing_permanent_failure(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test processing of a listing with permanent failure (404, etc.)."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher_instance = Mock()
        mock_enricher.return_value = mock_enricher_instance
        
        # Create worker
        worker = EbayWorker()
        
        # Mock channel and method
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        # Test listing data
        listing_data = {
            "listing_id": "12345",
            "title": "Test Item",
            "price": 100.0,
            "url": "https://example.com/item"
        }
        mock_body = json.dumps(listing_data).encode('utf-8')
        
        # Mock Playwright context with permanent failure
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
            
            mock_browser_type = Mock()
            mock_playwright_instance.chromium = mock_browser_type
            
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()
            
            mock_browser_type.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # Mock enricher to raise 404 error
            mock_enricher_instance.enrich_and_snapshot.side_effect = Exception("404 Not Found")
            
            # Process listing
            worker.process_listing(mock_channel, mock_method, None, mock_body)
            
            # Verify results - permanent failure should ACK
            assert worker.processed_count == 0
            assert worker.failed_count == 1
            
            # Verify ACK for permanent failure
            mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_process_listing_temporary_failure(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test processing of a listing with temporary failure (network, etc.)."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher_instance = Mock()
        mock_enricher.return_value = mock_enricher_instance
        
        # Create worker
        worker = EbayWorker()
        
        # Mock channel and method
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        # Test listing data
        listing_data = {
            "listing_id": "12345",
            "title": "Test Item",
            "price": 100.0,
            "url": "https://example.com/item"
        }
        mock_body = json.dumps(listing_data).encode('utf-8')
        
        # Mock Playwright context with temporary failure
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
            
            mock_browser_type = Mock()
            mock_playwright_instance.chromium = mock_browser_type
            
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()
            
            mock_browser_type.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # Mock enricher to raise temporary error (not timeout - that's permanent)
            mock_enricher_instance.enrich_and_snapshot.side_effect = Exception("Connection refused")
            
            # Process listing
            worker.process_listing(mock_channel, mock_method, None, mock_body)
            
            # Verify results - temporary failure should NACK
            assert worker.processed_count == 0
            assert worker.failed_count == 1
            
            # Verify NACK for temporary failure
            mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=True)

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_process_listing_invalid_json(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test processing of a listing with invalid JSON."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher.return_value = Mock()
        
        # Create worker
        worker = EbayWorker()
        
        # Mock channel and method
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        # Invalid JSON
        mock_body = b"invalid json"
        
        # Process listing
        worker.process_listing(mock_channel, mock_method, None, mock_body)
        
        # Verify results - should NACK for invalid JSON
        assert worker.processed_count == 0
        assert worker.failed_count == 1
        
        # Verify NACK for invalid JSON
        mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=True)

    @patch('scraper.worker.settings')
    @patch('scraper.worker.ListingEnricher')
    @patch('scraper.worker.get_queue_manager_from_env')
    def test_cleanup_profile(self, mock_queue_manager, mock_enricher, mock_settings):
        """Test profile cleanup functionality."""
        # Mock settings
        mock_settings.get_snapshot_dir.return_value = "/tmp/snapshots"
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock enricher
        mock_enricher.return_value = Mock()
        
        # Create worker
        worker = EbayWorker()
        worker.user_data_dir = "/tmp/test-profile"
        
        # Test cleanup with existing directory
        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:
            worker._cleanup_profile()
            mock_rmtree.assert_called_once_with("/tmp/test-profile")
        
        # Test cleanup with non-existing directory
        with patch('os.path.exists', return_value=False), \
             patch('shutil.rmtree') as mock_rmtree:
            worker._cleanup_profile()
            mock_rmtree.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
