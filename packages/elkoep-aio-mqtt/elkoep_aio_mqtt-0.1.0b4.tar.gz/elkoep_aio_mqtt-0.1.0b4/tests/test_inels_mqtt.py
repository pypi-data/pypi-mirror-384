from unittest.mock import AsyncMock

import pytest

from inelsmqtt import InelsMqtt


@pytest.fixture
def mock_publish():
    """Mock publish function."""
    return AsyncMock()


@pytest.fixture
def mock_subscribe():
    """Mock subscribe function."""
    return AsyncMock()


@pytest.fixture
def mock_unsubscribe():
    """Mock unsubscribe function."""
    return AsyncMock()


@pytest.fixture
def inels_mqtt(mock_publish, mock_subscribe, mock_unsubscribe):
    """Create InelsMqtt instance with mocked callbacks."""
    return InelsMqtt(mock_publish, mock_subscribe, mock_unsubscribe)


def test_instance_initialization(inels_mqtt, mock_publish, mock_subscribe, mock_unsubscribe):
    """Test initialization of InelsMqtt class."""
    assert inels_mqtt._InelsMqtt__ha_publish == mock_publish
    assert inels_mqtt._InelsMqtt__ha_subscribe == mock_subscribe
    assert inels_mqtt._InelsMqtt__ha_unsubscribe == mock_unsubscribe


@pytest.mark.asyncio
async def test_publish_successful(inels_mqtt, mock_publish):
    """Test successful publishing of a message."""
    topic = "inels/status/10e97f8b7d30/01/01E8"
    payload = "data"

    await inels_mqtt.publish(topic, payload)

    mock_publish.assert_called_once_with(topic, payload, 0, True)


@pytest.mark.asyncio
async def test_subscribe_successful(inels_mqtt, mock_subscribe):
    """Test successful subscription to a topic."""
    topic = "inels/status/10e97f8b7d30/01/01E8"

    await inels_mqtt.subscribe(topic)

    mock_subscribe.assert_called_once()


@pytest.mark.asyncio
async def test_unsubscribe_successful(inels_mqtt, mock_unsubscribe):
    """Test successful unsubscription from a topic."""
    topic = "inels/status/10e97f8b7d30/01/01E8"

    # First subscribe to create substate
    await inels_mqtt.subscribe(topic)

    assert inels_mqtt._substates != {}

    # Then unsubscribe
    await inels_mqtt.unsubscribe(topic)

    mock_unsubscribe.assert_called_once()

    assert inels_mqtt._substates == {}


def test_messages_property(inels_mqtt):
    """Test if messages property returns right data."""
    dictionary = {
        "inels/status/555555/02/34234524": "first",
        "inels/status/555555/02/34245242": "second",
        "inels/status/555555/03/45243523": "third",
        "inels/status/222222/02/85034495": "fourth",
    }

    inels_mqtt._InelsMqtt__messages = dictionary

    assert inels_mqtt.messages() is not None
    assert len(inels_mqtt.messages()) == 4
    assert inels_mqtt.messages() == dictionary


def test_last_value_property(inels_mqtt):
    """Test last_value method."""
    topic = "inels/status/555555/02/85034495"
    value = "test_value"

    inels_mqtt._InelsMqtt__last_values[topic] = value

    assert inels_mqtt.last_value(topic) == value
    assert inels_mqtt.last_value("nonexistent_topic") is None


def test_subscribe_listener(inels_mqtt):
    """Test listener subscription."""

    def dummy_callback(prm):
        """Dummy callback function"""
        return prm

    # Subscribe listeners with dummy callback
    inels_mqtt.subscribe_listener("inels/status/10e97f8b7d30/01/01E8", "uid_1", dummy_callback)
    inels_mqtt.subscribe_listener("inels/status/10e97f8b7d30/03/03E8", "uid_2", dummy_callback)

    # Assert that two listeners are subscribed
    assert len(inels_mqtt.list_of_listeners) == 2
    assert "uid_1" in inels_mqtt.list_of_listeners["10e97f8b7d30/01/01E8"]
    assert "uid_2" in inels_mqtt.list_of_listeners["10e97f8b7d30/03/03E8"]


def test_unsubscribe_listeners(inels_mqtt):
    """Test unsubscribe all listeners."""

    def dummy_callback(prm):
        """Dummy callback function"""
        return prm

    # Subscribe listeners
    inels_mqtt.subscribe_listener("inels/status/10e97f8b7d30/01/01E8", "uid_1", dummy_callback)
    inels_mqtt.subscribe_listener("inels/status/10e97f8b7d30/03/03E8", "uid_2", dummy_callback)

    # Check if two listeners are subscribed
    assert len(inels_mqtt.list_of_listeners) == 2

    # Unsubscribe all listeners
    inels_mqtt.unsubscribe_listeners()

    # Check if no listeners are left
    assert len(inels_mqtt.list_of_listeners) == 0


def test_on_message_callback(inels_mqtt):
    """Test the on_message callback function."""
    topic = "inels/status/10e97f8b7d30/01/01E8"
    payload = "test_payload"

    # Test the callback
    inels_mqtt.on_message(topic, payload)

    # Check that the message was stored
    assert inels_mqtt.messages()[topic] == payload
    assert inels_mqtt.last_value(topic) == payload
