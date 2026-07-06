from ..broker import broker
from ..constants import RoutingKey
from ..exchanges import exchange_log


async def publisher_log_register(message: dict):
    await broker.publish(
        exchange=exchange_log,
        routing_key=RoutingKey.LOG_REGISTER_ROUTING_KEY,
        message=message
    )
