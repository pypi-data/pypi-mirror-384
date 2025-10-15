"""Library specified for inels-mqtt."""

import asyncio
import copy
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Optional

from inelsmqtt.const import GATEWAY
from inelsmqtt.utils.core import ProtocolHandlerMapper

from .const import (
    DISCOVERY_TIMEOUT_IN_SEC,
    FRAGMENT_DEVICE_TYPE,
    FRAGMENT_STATE,
    MQTT_STATUS_TOPIC_PREFIX,
    MQTT_TOTAL_CONNECTED_TOPIC,
    MQTT_TOTAL_STATUS_TOPIC,
    TOPIC_FRAGMENTS,
    VERSION,
)

__version__ = VERSION

_LOGGER = logging.getLogger(__name__)

# when no topic were detected, then stop discovery
__DISCOVERY_TIMEOUT__ = DISCOVERY_TIMEOUT_IN_SEC


class InelsMqtt:
    """Wrapper for mqtt client."""

    def __init__(
        self,
        publish: Callable[
            [str, str | bytes | int | float | None, int | None, bool | None],
            Coroutine[Any, Any, None],
        ],
        subscribe: Callable[
            [dict[str, Any] | None, str, Callable[[str, str], None]],
            Coroutine[Any, Any, dict[str, Any]],
        ],
        unsubscribe: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """InelsMqtt instance initialization."""
        self.__ha_publish = publish
        self.__ha_subscribe = subscribe
        self.__ha_unsubscribe = unsubscribe

        self._substates: dict[str, dict[str, Any]] = {}

        self.__listeners: dict[str, dict[str, Callable[[Any], Any]]] = defaultdict(lambda: dict())
        self.__last_values = dict[str, str]()
        self.__messages = dict[str, Optional[str]]()
        self.__discovered = dict[str, Optional[str]]()
        self.on_message = self.__on_message

    def __on_message(self, topic: str, payload: str) -> None:
        """Callback function which is used for subscription."""
        message_parts = topic.split("/")

        device_type = message_parts[TOPIC_FRAGMENTS[FRAGMENT_DEVICE_TYPE]]
        message_type = message_parts[TOPIC_FRAGMENTS[FRAGMENT_STATE]]

        if device_type in ProtocolHandlerMapper.DEVICE_TYPE_MAP or device_type == "gw":
            # keep last value
            self.__last_values[topic] = copy.copy(self.__messages[topic]) if topic in self.__messages else payload
            self.__messages[topic] = payload

        if device_type == "gw" and message_type == "connected":
            mac = message_parts[2]
            for stripped_topic in list(self.__listeners):
                if stripped_topic.startswith(mac):
                    self.__notify_listeners(stripped_topic, True)
            return

        stripped_topic = "/".join(message_parts[2:])

        is_connected_message = message_type == "connected"

        if len(self.__listeners) > 0 and stripped_topic in self.__listeners:
            # This pass data change directely into the device.
            self.__notify_listeners(stripped_topic, is_connected_message)

    async def subscribe(
        self,
        topic: str,
    ) -> None:
        """Subscribe to selected topics."""
        # from all subscribed topic get substate
        substate = self._substates.get(topic)

        # call the ha mqtt client and get an substate update
        substate = await self.__ha_subscribe(substate, topic, self.on_message)

        # save the substate
        self._substates[topic] = substate

    async def publish(self, topic: str, payload: str, qos: int | None = 0, retain: bool | None = True) -> None:
        """Publish a MQTT message."""
        await self.__ha_publish(topic, payload, qos, retain)

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a selected topic."""
        # get the substate from the topic
        substate = self._substates.get(topic)

        # call the mqtt client to unsubscribe
        await self.__ha_unsubscribe(substate)

        # delete the substate
        del self._substates[topic]

    async def discovery_all(self) -> dict[str, Optional[str]]:
        """Discover all devices.
        Returns:
            dict[str, str]: Dictionary of all topics with their payloads
        """
        self.on_message = self.__on_discover

        topics_to_subscribe = [MQTT_TOTAL_CONNECTED_TOPIC, MQTT_TOTAL_STATUS_TOPIC]
        for topic in topics_to_subscribe:
            await self.subscribe(topic)

        await asyncio.sleep(__DISCOVERY_TIMEOUT__)

        for t in self.__discovered:
            self.__messages[MQTT_STATUS_TOPIC_PREFIX + t] = self.__discovered[t]

        for topic in topics_to_subscribe:
            await self.unsubscribe(topic)

        self.on_message = self.__on_message

        return self.__discovered

    def __on_discover(self, topic: str, payload: str) -> None:
        """Special callback function used only in discover_all function
        placed in on_message. It is the same as on_message callback func,
        but does different things.
        """
        _LOGGER.info("Found device from topic %s\n", topic)

        # pass only those who belong to known device types
        fragments = topic.split("/")
        device_type = fragments[TOPIC_FRAGMENTS[FRAGMENT_DEVICE_TYPE]]
        action = fragments[TOPIC_FRAGMENTS[FRAGMENT_STATE]]

        topic = topic.split("/")[2:]
        topic = "/".join(topic)

        if device_type in ProtocolHandlerMapper.DEVICE_TYPE_MAP:
            if action == "status":
                self.__discovered[topic] = payload
                self.__last_values[topic] = payload
                _LOGGER.info("Device of type %s found [status].\n", device_type)
            elif action == "connected":
                if topic not in self.__discovered:
                    # Setting to None ensures that it is tracked even if its status message is not received. It will be used for COM_TEST.
                    self.__discovered[topic] = None
                    self.__last_values[topic] = payload
                _LOGGER.info("Device of type %s found [connected].\n", device_type)
        else:
            if device_type == "gw" and action in ["connected", "status"]:
                if topic not in self.__discovered:
                    self.__discovered[topic] = GATEWAY
                    self.__last_values[topic] = payload
                    _LOGGER.info("Device of type %s found [gw].\n", device_type)
            elif device_type != "gw":
                _LOGGER.error("No handler found for device_type: %s", device_type)

    def messages(self) -> dict[str, Optional[str]]:
        """List of all messages

        Returns:
            dict[str, Optional[str]]: List of all messages (topics)
            from broker subscribed.
            It is key-value dictionary. Key is topic and value
            is payload of topic
        """
        return self.__messages

    def last_value(self, topic: str) -> Optional[str]:
        """Get last value of the selected topic

        Args:
            topic (str): topic name

        Returns:
            Optional[str]: last value of the topic, or None if not found
        """
        return self.__last_values.get(topic)

    @property
    def list_of_listeners(self) -> dict[str, dict[str, Callable[[Any], Any]]]:
        """List of listeners."""
        return self.__listeners

    def subscribe_listener(self, topic: str, unique_id: str, fnc: Callable[[Any], Any]) -> None:
        """Append new item into the datachange listener."""
        stripped_topic = "/".join(topic.split("/")[2:])
        self.__listeners[stripped_topic][unique_id] = fnc

    def unsubscribe_listeners(self) -> None:
        """Unsubscribe listeners."""
        self.__listeners.clear()

    async def unsubscribe_topics(self) -> None:
        """Unsubscribe from all MQTT topics."""
        for topic in list(self._substates.keys()):
            await self.unsubscribe(topic)

    def __notify_listeners(self, stripped_topic: str, is_connected_message: bool) -> None:
        """Notify listeners for a specific topic."""
        if len(self.__listeners[stripped_topic]) > 0:
            for unique_id in list(
                self.__listeners[stripped_topic]
            ):  # prevents the dictionary increased in size during iteration exception
                self.__listeners[stripped_topic][unique_id](is_connected_message)
