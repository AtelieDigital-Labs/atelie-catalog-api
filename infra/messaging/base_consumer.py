import json

import pika
import pika.adapters.blocking_connection

from .connection import get_connection


class RabbitMQConsumer:

    def __init__(self):
        self.connection = get_connection()
        self.channel = self.connection.channel()

    def register(
        self,
        exchange: str,
        queue: str,
        routing_key: str,
        callback,
        exchange_type: str = "topic",
        durable: bool = True,
        requeue: bool = True,
    ):

        self.channel.exchange_declare(
            exchange=exchange,
            exchange_type=exchange_type,
            durable=durable,
        )

        self.channel.queue_declare(
            queue=queue,
            durable=durable,
        )

        self.channel.queue_bind(
            exchange=exchange,
            queue=queue,
            routing_key=routing_key,
        )

        def wrapper(
            ch: pika.adapters.blocking_connection.BlockingChannel,
            method,
            properties,
            body,
        ):

            try:
                data = json.loads(body)

                callback(data)

                ch.basic_ack(
                    delivery_tag=method.delivery_tag
                )

            except Exception as error:

                print(
                    f"[ERROR] Failed to process message "
                    f"from queue '{queue}': {error}"
                )

                ch.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=requeue,
                )

        self.channel.basic_qos(
            prefetch_count=1
        )

        self.channel.basic_consume(
            queue=queue,
            on_message_callback=wrapper,
        )

        print(
            f"[CONSUMER] Registered "
            f"queue='{queue}' "
            f"routing_key='{routing_key}'"
        )

    def start(self):

        print("[CONSUMER] Waiting for messages...")

        try:
            self.channel.start_consuming()

        except KeyboardInterrupt:

            print("[CONSUMER] Stopping consumer...")

            self.channel.stop_consuming()

        finally:

            if self.connection and self.connection.is_open:
                self.connection.close()

            print("[CONSUMER] Connection closed.")