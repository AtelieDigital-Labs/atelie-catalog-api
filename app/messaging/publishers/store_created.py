from infra.messaging.base_publisher import RabbitMQPublisher
from infra.messaging.constants import STORE_CREATED_QUEUE, STORE_CREATED_ROUTING_KEY
from dataclasses import asdict
from ..events.store_created import StoreCreatedEvent

def publisher_store_created(event: StoreCreatedEvent):
    publisher = RabbitMQPublisher()

    publisher.publish(
        queue=STORE_CREATED_QUEUE,
        routing_key=STORE_CREATED_ROUTING_KEY,
        message=asdict(event)
    )