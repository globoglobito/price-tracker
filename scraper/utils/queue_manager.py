"""
RabbitMQ queue management for distributed scraping.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)

try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False
    logger.warning("pika not installed - queue functionality disabled")


class QueueManager:
    """Manages RabbitMQ connections and operations for distributed scraping."""
    
    def __init__(self, 
                 host: str = "rabbitmq-service",
                 port: int = 5672,
                 username: str = "admin", 
                 password: str = "admin123",
                 vhost: str = "price-tracker"):
        """
        Initialize queue manager.
        
        Args:
            host: RabbitMQ host (default: rabbitmq-service for K8s)
            port: RabbitMQ port (default: 5672)
            username: RabbitMQ username
            password: RabbitMQ password  
            vhost: RabbitMQ virtual host
        """
        if not PIKA_AVAILABLE:
            raise ImportError("pika library required for queue operations. Install with: pip install pika")
            
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.connection = None
        self.channel = None
        
        # Queue names
        self.ENRICHMENT_QUEUE = "listing_enrichment"
        self.DEAD_LETTER_QUEUE = "listing_enrichment_dlq"
        
    def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=credentials,
                heartbeat=300,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues
            self._declare_queues()
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
            
    def disconnect(self) -> None:
        """Close RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
            
    def _declare_queues(self) -> None:
        """Declare all necessary queues with appropriate settings."""
        if not self.channel:
            raise RuntimeError("No channel available - call connect() first")
            
        # Dead letter queue (for failed messages)
        self.channel.queue_declare(
            queue=self.DEAD_LETTER_QUEUE,
            durable=True
        )
        
        # Main enrichment queue with DLQ routing
        self.channel.queue_declare(
            queue=self.ENRICHMENT_QUEUE,
            durable=True,
            arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': self.DEAD_LETTER_QUEUE,
                'x-message-ttl': 43200000,  # 12 hours TTL
                'x-max-retries': 3
            }
        )
        
        logger.info("Queues declared successfully")
        
    def publish_listing_for_enrichment(self, listing_data: Dict[str, Any]) -> bool:
        """
        Publish a single listing for enrichment.
        
        Args:
            listing_data: Dictionary containing listing information
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.channel:
            logger.error("No channel available - call connect() first")
            return False
            
        try:
            message = json.dumps(listing_data)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.ENRICHMENT_QUEUE,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    timestamp=int(time.time())
                )
            )
            
            logger.debug(f"Published listing for enrichment: {listing_data.get('listing_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish listing: {e}")
            return False
            
    def publish_batch_for_enrichment(self, listings: List[Dict[str, Any]]) -> int:
        """
        Publish multiple listings for enrichment.
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            Number of successfully published listings
        """
        published_count = 0
        
        for listing in listings:
            if self.publish_listing_for_enrichment(listing):
                published_count += 1
                
        logger.info(f"Published {published_count}/{len(listings)} listings for enrichment")
        return published_count
        
    def get_queue_message_count(self, queue_name: str) -> int:
        """Get the number of messages in a queue."""
        if not self.channel:
            logger.error("No channel available - call connect() first")
            return 0
        
        try:
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            return method.method.message_count
        except Exception as e:
            logger.error(f"Failed to get queue count for {queue_name}: {e}")
            return 0

    def consume_listing_for_enrichment(self, callback_func, auto_ack: bool = False, max_empty_polls: int = 10):
        """
        Consume listings from enrichment queue.
        
        Args:
            callback_func: Function to call for each message (ch, method, properties, body)
            auto_ack: Whether to automatically acknowledge messages
            max_empty_polls: Number of empty polls before graceful shutdown
        """
        if not self.channel:
            logger.error("No channel available - call connect() first")
            return
            
        self.channel.basic_qos(prefetch_count=1)  # Process one message at a time
        
        self.channel.basic_consume(
            queue=self.ENRICHMENT_QUEUE,
            on_message_callback=callback_func,
            auto_ack=auto_ack
        )
        
        logger.info("Starting to consume enrichment tasks...")
        empty_polls = 0
        
        try:
            while True:
                # Check if there are messages in the queue
                message_count = self.get_queue_message_count(self.ENRICHMENT_QUEUE)
                
                if message_count == 0:
                    empty_polls += 1
                    logger.info(f"Queue empty, poll {empty_polls}/{max_empty_polls}")
                    
                    if empty_polls >= max_empty_polls:
                        logger.info("Queue empty for too long, gracefully shutting down worker")
                        break
                        
                    # Wait a bit before checking again
                    import time
                    time.sleep(5)
                    continue
                else:
                    empty_polls = 0  # Reset counter when messages are found
                
                # Process messages with timeout
                self.connection.process_data_events(time_limit=10)
                
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            try:
                self.channel.stop_consuming()
            except Exception:
                pass
            
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue message counts
        """
        if not self.channel:
            logger.error("No channel available - call connect() first")
            return {}
            
        try:
            main_queue = self.channel.queue_declare(queue=self.ENRICHMENT_QUEUE, passive=True)
            dlq_queue = self.channel.queue_declare(queue=self.DEAD_LETTER_QUEUE, passive=True)
            
            return {
                'enrichment_queue_messages': main_queue.method.message_count,
                'dead_letter_queue_messages': dlq_queue.method.message_count
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}


def get_queue_manager_from_env() -> QueueManager:
    """Create QueueManager instance from environment variables."""
    return QueueManager(
        host=os.environ.get("RABBITMQ_HOST", "rabbitmq-service"),
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        username=os.environ.get("RABBITMQ_USERNAME", "admin"),
        password=os.environ.get("RABBITMQ_PASSWORD", "admin123"),
        vhost=os.environ.get("RABBITMQ_VHOST", "price-tracker")
    )
