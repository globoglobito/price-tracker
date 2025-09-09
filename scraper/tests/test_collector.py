"""
Tests for collector module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.collector import EbayCollector


class TestEbayCollector:
    """Test cases for EbayCollector class."""

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    def test_collector_initialization(self, mock_queue_manager, mock_scraper, mock_settings):
        """Test collector initializes correctly with proper configuration."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 5
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = "/tmp/test"
        mock_settings.get_slow_mo_ms.return_value = 100
        mock_settings.get_debug_snapshot_dir.return_value = "/tmp/debug"
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock scraper
        mock_scraper.return_value = Mock()
        
        # Create collector
        collector = EbayCollector()
        
        # Verify initialization
        assert collector.search_term == "Test Search"
        assert collector.max_pages == 5
        assert collector.headless is True
        assert collector.browser_name == "chromium"
        assert collector.user_data_dir is not None
        assert collector.slow_mo_ms == 100
        assert collector.debug_snapshot_dir == "/tmp/debug"
        assert collector.timeout_ms == 30000
        
        # Verify scraper was initialized correctly
        mock_scraper.assert_called_once()
        call_args = mock_scraper.call_args
        assert call_args[1]['search_term'] == "Test Search"
        assert call_args[1]['max_pages'] == 5
        assert call_args[1]['headless'] is True
        assert call_args[1]['browser_name'] == "chromium"
        assert call_args[1]['enrich_limit'] == 0  # No enrichment in collector
        assert call_args[1]['snapshot_dir'] is None  # No snapshots in collector

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    def test_collector_without_user_data_dir(self, mock_queue_manager, mock_scraper, mock_settings):
        """Test collector works without user data directory."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 2
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None  # No user data dir
        mock_settings.get_slow_mo_ms.return_value = 0
        mock_settings.get_debug_snapshot_dir.return_value = None
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock scraper
        mock_scraper.return_value = Mock()
        
        # Create collector
        collector = EbayCollector()
        
        # Verify user_data_dir is None
        assert collector.user_data_dir is None

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    @patch('scraper.collector.upsert_listings')
    @patch('scraper.collector.get_or_create_search')
    def test_collect_and_queue_listings_success(self, mock_get_search, mock_upsert, 
                                               mock_queue_manager, mock_scraper, mock_settings):
        """Test successful collection and queueing of listings."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 2
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        mock_settings.get_debug_snapshot_dir.return_value = None
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue = Mock()
        mock_queue_manager.return_value = mock_queue
        mock_queue.publish_batch_for_enrichment.return_value = 3
        mock_queue.get_queue_stats.return_value = {"messages": 3}
        
        # Mock scraper
        mock_scraper_instance = Mock()
        mock_scraper.return_value = mock_scraper_instance
        mock_listings = [
            {"listing_id": "1", "title": "Item 1", "price": 100},
            {"listing_id": "2", "title": "Item 2", "price": 200},
            {"listing_id": "3", "title": "Item 3", "price": 300}
        ]
        mock_scraper_instance.scrape.return_value = mock_listings
        
        # Mock database operations
        mock_get_search.return_value = 1
        mock_upsert.return_value = 3
        
        # Create collector and run
        collector = EbayCollector()
        stats = collector.collect_and_queue_listings()
        
        # Verify results
        assert stats['listings_found'] == 3
        assert stats['listings_upserted'] == 3
        assert stats['listings_queued'] == 3
        assert stats['errors'] == 0
        
        # Verify method calls
        mock_scraper_instance.scrape.assert_called_once()
        mock_get_search.assert_called_once_with("Test Search", "ebay")
        mock_upsert.assert_called_once()
        mock_queue.publish_batch_for_enrichment.assert_called_once_with(mock_listings)
        mock_queue.get_queue_stats.assert_called_once()

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    def test_collect_and_queue_listings_no_listings(self, mock_queue_manager, mock_scraper, mock_settings):
        """Test collection when no listings are found."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 2
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        mock_settings.get_debug_snapshot_dir.return_value = None
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue = Mock()
        mock_queue_manager.return_value = mock_queue
        
        # Mock scraper - return empty list
        mock_scraper_instance = Mock()
        mock_scraper.return_value = mock_scraper_instance
        mock_scraper_instance.scrape.return_value = []
        
        # Create collector and run
        collector = EbayCollector()
        stats = collector.collect_and_queue_listings()
        
        # Verify results
        assert stats['listings_found'] == 0
        assert stats['listings_upserted'] == 0
        assert stats['listings_queued'] == 0
        assert stats['errors'] == 0

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    def test_collect_and_queue_listings_db_error(self, mock_queue_manager, mock_scraper, mock_settings):
        """Test collection when database operations fail."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 2
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = None
        mock_settings.get_slow_mo_ms.return_value = 0
        mock_settings.get_debug_snapshot_dir.return_value = None
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue = Mock()
        mock_queue_manager.return_value = mock_queue
        mock_queue.publish_batch_for_enrichment.return_value = 2
        mock_queue.get_queue_stats.return_value = {"messages": 2}
        
        # Mock scraper
        mock_scraper_instance = Mock()
        mock_scraper.return_value = mock_scraper_instance
        mock_listings = [
            {"listing_id": "1", "title": "Item 1", "price": 100},
            {"listing_id": "2", "title": "Item 2", "price": 200}
        ]
        mock_scraper_instance.scrape.return_value = mock_listings
        
        # Mock database operations to fail
        with patch('scraper.collector.get_or_create_search', side_effect=Exception("DB Error")):
            # Create collector and run
            collector = EbayCollector()
            stats = collector.collect_and_queue_listings()
            
            # Verify results - should continue with queueing despite DB error
            assert stats['listings_found'] == 2
            assert stats['listings_upserted'] == 0
            assert stats['listings_queued'] == 2
            assert stats['errors'] == 1  # DB error counted

    @patch('scraper.collector.settings')
    @patch('scraper.collector.EbayBrowserScraper')
    @patch('scraper.collector.get_queue_manager_from_env')
    def test_cleanup_profile(self, mock_queue_manager, mock_scraper, mock_settings):
        """Test profile cleanup functionality."""
        # Mock settings
        mock_settings.get_search_term.return_value = "Test Search"
        mock_settings.get_max_pages.return_value = 2
        mock_settings.is_headless.return_value = True
        mock_settings.get_browser_type.return_value = "chromium"
        mock_settings.get_user_data_dir.return_value = "/tmp/test"
        mock_settings.get_slow_mo_ms.return_value = 0
        mock_settings.get_debug_snapshot_dir.return_value = None
        mock_settings.get_timeout_ms.return_value = 30000
        
        # Mock queue manager
        mock_queue_manager.return_value = Mock()
        
        # Mock scraper
        mock_scraper.return_value = Mock()
        
        # Create collector
        collector = EbayCollector()
        
        # Test cleanup with existing directory
        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:
            collector._cleanup_profile()
            mock_rmtree.assert_called_once_with(collector.user_data_dir)
        
        # Test cleanup with non-existing directory
        with patch('os.path.exists', return_value=False), \
             patch('shutil.rmtree') as mock_rmtree:
            collector._cleanup_profile()
            mock_rmtree.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
