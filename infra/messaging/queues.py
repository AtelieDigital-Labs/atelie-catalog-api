from faststream.rabbit import RabbitQueue
from .constants import RoutingKey, Queue
from .exchanges import exchange_dlq

FIFITEEN_MINUTES_IN_MILLISECONDS = 5 * 60 * 1000

product_reservation_queue = RabbitQueue(
    name=Queue.STOCK_RESERVATION_QUEUE,
    routing_key=RoutingKey.ORDER_CREATED_ROUTING_KEY,
    durable=True,
)

product_reservation_ttl_queue = RabbitQueue(
    name=Queue.STOCK_RESERVATION_TTL_QUEUE,
    routing_key=RoutingKey.ORDER_CREATED_ROUTING_KEY,
    durable=True,
    arguments={
        "x-message-ttl": FIFITEEN_MINUTES_IN_MILLISECONDS, 
        "x-dead-letter-exchange": exchange_dlq.name,
        "x-dead-letter-routing-key": RoutingKey.STOCK_RESERVATION_EXPIRE_ROUTING_KEY
    }
)

product_reservation_dlq = RabbitQueue(
    name=Queue.PRODUCT_RESERVATION_EXPIRE_DLQ,
    routing_key=RoutingKey.STOCK_RESERVATION_EXPIRE_ROUTING_KEY,
    durable=True
)

product_reservation_confirm_queue = RabbitQueue(
    name=Queue.STOCK_RESERVATION_CONFIRM_QUEUE,
    routing_key=RoutingKey.ORDER_PAID_ROUTING_KEY,
    durable=True
)