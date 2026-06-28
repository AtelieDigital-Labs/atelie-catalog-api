from ..broker import broker
from ..events.store_created import StoreCreatedEvent
from ..exchanges import exchange_catalogs
from ..constants import RoutingKey
from dataclasses import asdict
from faststream.rabbit import RabbitBroker

# async def publisher_store_created(event: StoreCreatedEvent):
#     await broker.publish(
#         exchange=exchange_catalogs,
#         routing_key=RoutingKey.STORE_CREATED_ROUTING_KEY,
#         message=asdict(event)
#     )

async def publisher_store_created(event: StoreCreatedEvent):
        await broker.publish(
            message=asdict(event),
            exchange=exchange_catalogs,
            routing_key=RoutingKey.STORE_CREATED_ROUTING_KEY
        )