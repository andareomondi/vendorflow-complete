import json
import paho.mqtt.client as mqtt
from django.conf import settings
from django.apps import apps
import logging
import threading
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MQTTClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize from settings.py
        self.client = mqtt.Client(
            client_id=getattr(settings, "MQTT_CLIENT_ID", "django_iot_server")
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Connection configuration
        self.broker = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.username = settings.MQTT_BROKER_USER
        self.password = settings.MQTT_BROKER_PASSWORD
        self.keepalive = getattr(settings, "MQTT_KEEPALIVE", 60)

        # Topic configuration
        self.vending_topic = getattr(settings, "MQTT_VENDING_TOPIC", "vending/+/status")
        self.relay_topic = getattr(settings, "MQTT_RELAY_TOPIC", "relay/+/status")

        # WebSocket
        self.channel_layer = get_channel_layer()
        self._initialized = True

    def start(self):
        """Connect with settings from settings.py"""
        try:
            # if self.username and self.password:
            #     self.client.username_pw_set(self.username, self.password)

            self.client.connect(
                host="127.0.0.1", port=self.port, keepalive=self.keepalive
            )
            self.client.loop_start()
            logger.info(f"Connected to {self.broker}:{self.port} as {self.username}")
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client stopped")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            # print('connected')
            client.subscribe(self.vending_topic)
            client.subscribe(self.relay_topic)
            logger.info(f"Subscribed to: {self.vending_topic}, {self.relay_topic}")
        else:
            logger.error(f"Connection failed (rc={rc})")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            # Determine device type and ID
            if topic.startswith("vending/"):
                self.process_vending_message(topic, payload)
            elif topic.startswith("relay/"):
                print("thatis a bingo")
                self.process_relay_message(topic, payload)

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")

    def process_vending_message(self, topic, payload):
        """Handle vending machine data with strict validation"""
        try:
            data = json.loads(payload)
            serial_no = topic.split("/")[1]  # Extract from vending/{serial_no}/status

            # Validate required fields
            required_fields = [
                "serial_no",
                "amount",
                "volume",
                "total_amount",
                "total_volume",
                "stock",
            ]
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields")

            # Check device registration
            Machine = apps.get_model("base", "Machine")
            if not Machine.objects.filter(serial_number=serial_no).exists():
                logger.warning(f"Unregistered vending machine: {serial_no}")
                return

            # Process transaction
            Transaction = apps.get_model("base", "Transaction")
            machine = Machine.objects.get(serial_number=serial_no)

            Transaction.objects.create(
                machine=machine,
                amount=float(data["amount"]),
                volume=float(data["volume"]),
                token_used=1,
            )

            # Update machine status
            machine.total_amount = float(data["total_amount"])
            machine.total_volume = float(data["total_volume"])
            machine.remaining_tokens = int(data["stock"])
            machine.save()

            # WebSocket notification
            self.notify_websocket(
                group=f"vending_{serial_no}",
                message={
                    "type": "vending_update",
                    "machine": {
                        "id": machine.id,
                        "serial_number": serial_no,
                        "remaining_tokens": machine.remaining_tokens,
                        "total_amount": data["total_amount"],
                        "total_volume": data["total_volume"],
                    },
                },
            )

        except Exception as e:
            logger.error(f"Vending processing error: {str(e)}")

    def process_relay_message(self, topic, payload):
        """Handle relay device updates with channel validation"""
        try:
            data = json.loads(payload)
            print(data)
            device_id = topic.split("/")[1]  # Extract from relay/{device_id}/status

            # Check device registration
            RelayDevice = apps.get_model("base", "RelayDevice")
            if not RelayDevice.objects.filter(device_id=device_id).exists():
                print("doesnot exist")
                logger.warning(f"Unregistered relay device: {device_id}")
                return
            print("exists")

            # Process each channel
            RelayChannel = apps.get_model("base", "RelayChannel")
            device = RelayDevice.objects.get(device_id=device_id)
            print(device)

            for key, value in data.items():
                if key.startswith(("IN_", "OUT_")):
                    channel_type = "IN" if key.startswith("IN_") else "OUT"
                    channel_num = int(key.split("_")[1])

                    channel, _ = RelayChannel.objects.update_or_create(
                        device=device,
                        channel_type=channel_type,
                        channel_number=channel_num,
                        defaults={"state": value.upper()},
                    )

                    # WebSocket notification
                    self.notify_websocket(
                        group=f"relay_{device_id}",
                        message={
                            "type": "channel_update",
                            "channel": {
                                "id": channel.id,
                                "device_id": device_id,
                                "channel_type": channel_type,
                                "channel_number": channel_num,
                                "state": value.upper(),
                            },
                        },
                    )

        except Exception as e:
            logger.error(f"Relay processing error: {str(e)}")

    def notify_websocket(self, group, message):
        """Send real-time updates via WebSocket"""
        try:
            async_to_sync(self.channel_layer.group_send)(group, message)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnect (rc={rc}), reconnecting...")
            threading.Timer(5, self.start).start()  # Reconnect after 5 seconds


# Singleton instance
mqtt_client = MQTTClient()


def start_mqtt():
    mqtt_client.start()


def stop_mqtt():
    mqtt_client.stop()
