"""Kafka message queue consumer."""
# pylint: disable=broad-exception-caught
import time
from typing import Callable, Optional, List, Generator
from kafka import KafkaConsumer
from kafka.errors import KafkaTimeoutError
from mcpuniverse.common.logger import get_logger
from mcpuniverse.pipeline.mq.base import BaseConsumer


class Consumer(BaseConsumer):
    """Kafka consumer with robust error handling and generator-based message consumption."""

    def __init__(
            self,
            host: str,
            port: int,
            topic: str,
            value_deserializer: Callable,
            key_deserializer: Optional[Callable] = None,
            bootstrap_servers: Optional[List[str]] = None,
            group_id: str = "mcpuniverse-group",
            auto_offset_reset: str = "earliest",
            enable_auto_commit: bool = True,
            **kwargs
    ):
        """
        Initialize Kafka consumer with production-ready settings.
        
        Args:
            host: Kafka broker host.
            port: Kafka broker port.
            topic: Topic to subscribe to.
            value_deserializer: Function to deserialize message values.
            key_deserializer: Function to deserialize message keys.
            bootstrap_servers: List of bootstrap servers (overrides host:port).
            group_id: Consumer group ID.
            auto_offset_reset: Offset reset strategy ('earliest', 'latest', 'none').
            enable_auto_commit: Whether to auto-commit offsets.
            **kwargs: Additional KafkaConsumer configuration.
        """
        super().__init__(host=host, port=port, topic=topic, value_deserializer=value_deserializer)
        self._logger = get_logger(self.__class__.__name__)

        servers = bootstrap_servers if bootstrap_servers else [f"{host}:{port}"]
        config = {
            "bootstrap_servers": servers,
            "group_id": group_id,
            "auto_offset_reset": auto_offset_reset,
            "enable_auto_commit": enable_auto_commit,
            "value_deserializer": value_deserializer,
            **kwargs
        }
        if key_deserializer:
            config["key_deserializer"] = key_deserializer

        try:
            self._client = KafkaConsumer(topic, **config)
            self._logger.info("Kafka consumer initialized successfully for topics: %s", self._topic)
        except Exception as e:
            self._logger.error("Failed to initialize Kafka consumer: %s", str(e))
            raise

    def consume_messages(
            self,
            timeout_ms: int = 1000,
            max_messages: Optional[int] = None,
            **kwargs
    ) -> Generator:
        """
        Generator that yields messages from Kafka topics.
        
        Args:
            timeout_ms: Timeout for polling messages.
            max_messages: Maximum number of messages to consume (None for unlimited).
            
        Yields:
            Deserialized message values.
        """
        message_count = 0

        while True:
            if max_messages is not None and message_count >= max_messages:
                self._logger.info("Reached maximum message limit: %d", max_messages)
                break

            try:
                message_batch = self._client.poll(
                    timeout_ms=timeout_ms,
                    max_records=self._client.config.get('max_poll_records', 500)
                )
                if not message_batch:
                    continue

                for _, messages in message_batch.items():
                    for message in messages:
                        self._logger.debug(
                            "Received message from topic=%s partition=%s offset=%s",
                            message.topic,
                            message.partition,
                            message.offset
                        )
                        yield message.value
                        message_count += 1
                        if max_messages is not None and message_count >= max_messages:
                            return

            except KafkaTimeoutError:
                self._logger.debug("Poll timeout, continuing...")
                time.sleep(1)
            except Exception as e:
                self._logger.error("Unexpected error during poll: %s", str(e))
                time.sleep(5)

    def seek_to_beginning(self, partitions: Optional[List] = None):
        """
        Seek to the beginning of topics/partitions.
        
        Args:
            partitions: Specific partitions to seek (None for all assigned partitions).
        """
        try:
            if partitions:
                self._client.seek_to_beginning(*partitions)
            else:
                self._client.seek_to_beginning()
            self._logger.info("Seeked to beginning of partitions")
        except Exception as e:
            self._logger.error("Error seeking to beginning: %s", str(e))

    def seek_to_end(self, partitions: Optional[List] = None):
        """
        Seek to the end of topics/partitions.
        
        Args:
            partitions: Specific partitions to seek (None for all assigned partitions).
        """
        try:
            if partitions:
                self._client.seek_to_end(*partitions)
            else:
                self._client.seek_to_end()
            self._logger.info("Seeked to end of partitions")
        except Exception as e:
            self._logger.error("Error seeking to end: %s", str(e))

    def close(self, timeout: Optional[float] = None, **kwargs):
        """
        Close the consumer and release resources.
        
        Args:
            timeout: Maximum time to wait for close completion.
        """
        try:
            self._client.close(timeout_ms=timeout)
            self._logger.info("Kafka consumer closed successfully")
        except Exception as e:
            self._logger.error("Error closing Kafka consumer: %s", str(e))
