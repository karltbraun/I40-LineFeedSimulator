from __future__ import annotations

import json
import logging

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttPublisher:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="linefeed-simulator")

    def connect(self) -> None:
        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()
        logger.info("Connected to MQTT broker at %s:%d", self._host, self._port)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Disconnected from MQTT broker")

    def publish(self, topic: str, value: float | int | str) -> None:
        # Integers must be coerced to float so json.dumps produces {"value": 2.0}
        # not {"value": 2}. InfluxDB line protocol treats bare integers as int type,
        # which conflicts with the float schema established by decimal values.
        if isinstance(value, int) and not isinstance(value, bool):
            value = float(value)
        payload = json.dumps({"value": value})
        self._client.publish(topic, payload, qos=1)
