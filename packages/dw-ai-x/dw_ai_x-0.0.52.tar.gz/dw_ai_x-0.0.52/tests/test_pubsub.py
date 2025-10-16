import pytest
import json
import base64

from google.cloud import pubsub_v1
from unittest.mock import patch, MagicMock

from commons.utils.pubsub import PubSubClient
from commons.schemas.pubsub_msg import PubSubMessage

@pytest.fixture
def pubsub_client():
    with patch('commons.utils.pubsub.pubsub_v1.PublisherClient') as MockPublisherClient:
        yield PubSubClient()

def test_publish_message(pubsub_client):
    message = {"key": "value"}
    with patch.object(pubsub_client.publisher, 'publish', return_value=MagicMock(result=lambda: None)) as mock_publish:
        pubsub_client.publish_message(message)
        mock_publish.assert_called_once_with(pubsub_client.topic_path, message=json.dumps(message).encode("utf-8"))

def test_read_message(pubsub_client):
    pubsub_message = PubSubMessage(subscription="test-subscription", message={"data": base64.b64encode(json.dumps({"key": "value"}).encode("utf-8")).decode("utf-8")})
    response = pubsub_client.read_message(pubsub_message)