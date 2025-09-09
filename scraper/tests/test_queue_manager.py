"""
Tests for queue manager module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.utils.queue_manager import QueueManager, get_queue_manager_from_env


class TestQueueManager:
    """Test cases for QueueManager class."""

    def test_queue_manager_initialization(self):
        """Test queue manager initializes correctly."""
        # Create queue manager
        queue_manager = QueueManager(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            vhost="test-vhost"
        )
        
        # Verify initialization
        assert queue_manager.host == "localhost"
        assert queue_manager.port == 5672
        assert queue_manager.username == "guest"
        assert queue_manager.password == "guest"
        assert queue_manager.vhost == "test-vhost"
        assert queue_manager.connection is None
        assert queue_manager.channel is None

    def test_get_queue_manager_from_env(self):
        """Test creating queue manager from environment variables."""
        # Mock environment variables
        with patch.dict(os.environ, {
            'RABBITMQ_HOST': 'test-host',
            'RABBITMQ_PORT': '5673',
            'RABBITMQ_USERNAME': 'test-user',
            'RABBITMQ_PASSWORD': 'test-pass',
            'RABBITMQ_QUEUE_NAME': 'test-queue'
        }):
            # Create queue manager from env
            queue_manager = get_queue_manager_from_env()
            
            # Verify initialization
            assert queue_manager.host == 'test-host'
            assert queue_manager.port == 5673
            assert queue_manager.username == 'test-user'
            assert queue_manager.password == 'test-pass'
            assert queue_manager.vhost == 'price-tracker'  # Default vhost

    def test_get_queue_manager_from_env_defaults(self):
        """Test creating queue manager with default values."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Create queue manager from env
            queue_manager = get_queue_manager_from_env()
            
            # Verify default values
            assert queue_manager.host == 'rabbitmq-service'
            assert queue_manager.port == 5672
            assert queue_manager.username == 'admin'
            assert queue_manager.password == 'admin123'
            assert queue_manager.vhost == 'price-tracker'

    def test_queue_manager_without_pika(self):
        """Test queue manager behavior when pika is not available."""
        # Mock pika import failure
        with patch('scraper.utils.queue_manager.PIKA_AVAILABLE', False):
            with pytest.raises(ImportError):
                QueueManager(
                    host="localhost",
                    port=5672,
                    username="guest",
                    password="guest",
                    vhost="test-vhost"
                )

    def test_publish_batch_for_enrichment_empty_list(self):
        """Test publishing empty batch."""
        queue_manager = QueueManager(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            vhost="test-vhost"
        )
        
        # Test with empty list
        count = queue_manager.publish_batch_for_enrichment([])
        assert count == 0

    def test_publish_batch_for_enrichment_single_item(self):
        """Test publishing single item batch."""
        queue_manager = QueueManager(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            vhost="test-vhost"
        )
        
        # Test with single item
        listings = [{"listing_id": "1", "title": "Item 1"}]
        
        # Mock the publish_listing_for_enrichment method
        with patch.object(queue_manager, 'publish_listing_for_enrichment') as mock_publish:
            count = queue_manager.publish_batch_for_enrichment(listings)
            
            # Verify results
            assert count == 1
            mock_publish.assert_called_once()

    def test_publish_batch_for_enrichment_multiple_items(self):
        """Test publishing multiple items batch."""
        queue_manager = QueueManager(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            vhost="test-vhost"
        )
        
        # Test with multiple items
        listings = [
            {"listing_id": "1", "title": "Item 1"},
            {"listing_id": "2", "title": "Item 2"},
            {"listing_id": "3", "title": "Item 3"}
        ]
        
        # Mock the publish_listing_for_enrichment method
        with patch.object(queue_manager, 'publish_listing_for_enrichment') as mock_publish:
            count = queue_manager.publish_batch_for_enrichment(listings)
            
            # Verify results
            assert count == 3
            assert mock_publish.call_count == 3

    def test_publish_batch_for_enrichment_with_exception(self):
        """Test publishing batch when some items fail."""
        queue_manager = QueueManager(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            vhost="test-vhost"
        )
        
        # Test with items that will cause exceptions
        listings = [
            {"listing_id": "1", "title": "Item 1"},
            {"listing_id": "2", "title": "Item 2"}
        ]
        
        # Mock publish_listing_for_enrichment to fail on second item
        def side_effect(item):
            if item["listing_id"] == "2":
                return False  # Return False for failure
            return True  # Return True for success
        
        with patch.object(queue_manager, 'publish_listing_for_enrichment', side_effect=side_effect):
            count = queue_manager.publish_batch_for_enrichment(listings)
            
            # Should return count of successful publishes
            assert count == 1


if __name__ == "__main__":
    pytest.main([__file__])