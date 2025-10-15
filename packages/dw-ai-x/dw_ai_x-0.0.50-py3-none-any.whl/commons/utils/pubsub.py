"""
A client for Google Cloud Pub/Sub.

This client provides methods to publish messages to a Pub/Sub topic.

Attributes:
    publisher (pubsub_v1.PublisherClient): The Pub/Sub publisher client.
    topic_path (str): The fully qualified identifier of the Pub/Sub topic.
    logger (logging.Logger): The logger instance for this class.
"""

import json
import base64

from google.cloud import pubsub_v1
from google.api_core import retry

from ..utils import constants as kk
import logging
from ..schemas.pubsub_msg import PubSubMessage


class PubSubClient:

    def __init__(self, project_id: str = kk.PROJECT_ID, topic_id: str = kk.TOPIC_ID):
        """Initialize Pub/Sub client.

        Args:
            project_id (str): GCP project ID
            topic_id (str): Pub/Sub topic ID
        """
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.publisher.close()

    @retry.Retry()
    def publish_message(self, message: dict):
        """Publish a message to a Pub/Sub topic.

        Args:
            message (dict): Message to be published
            subscription (str): Name of the subscription to publish the message to
        """
        self.logger.info(f"Publishing message to Pub/Sub topic: {self.topic_path}")

        message_json = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.topic_path, data=message_json)
        future.result()

        self.logger.info("Message published successfully")

    @retry.Retry()
    def read_message(self, pubsub_message: PubSubMessage):
        """Read a message from a Pub/Sub subscription.

        Args:
            pubsub_message (PubSubMessage): Message to be read
        """
        self.logger.info(
            f"Reading message from Pub/Sub subscription: {pubsub_message.subscription}"
        )

        encoded_data = pubsub_message.message["data"]
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        response = json.loads(decoded_data)

        self.logger.info(f"Message received: {response}")

        return response
