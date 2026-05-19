import json

from .connection import get_connection
from .constants import CATALOG_EXCHANGE


class RabbitMQPublisher:
    def publish(self, queue: str, routing_key: str, message: dict):
        connection = get_connection()

        channel = connection.channel()

        channel.exchange_declare(
            exchange=CATALOG_EXCHANGE,
            exchange_type="topic",
            durable=True,
        )

        channel.queue_declare(
            queue=queue,
            durable=True,
        )

        channel.queue_bind(
            exchange=CATALOG_EXCHANGE,
            queue=queue,
            routing_key=routing_key,
        )

        channel.basic_publish(
            exchange=CATALOG_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(message),
        )

        connection.close()