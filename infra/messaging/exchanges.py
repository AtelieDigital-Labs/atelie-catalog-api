from faststream.rabbit import RabbitExchange, ExchangeType, RabbitBroker
from .constants import Exchange

exchange_accounts = RabbitExchange(
    name=Exchange.ACCOUNTS_EXCHANGE,
    type=ExchangeType.TOPIC,
    durable=True
)

exchange_catalogs = RabbitExchange(
    name=Exchange.CATALOG_EXCHANGE,
    type=ExchangeType.TOPIC,
    durable=True
)

exchange_orders = RabbitExchange(
    name=Exchange.ORDER_EXCHANGE,
    type=ExchangeType.TOPIC,
    durable=True
)

async def declare_exchange(broker: RabbitBroker):
    await broker.declare_exchange(exchange_accounts)
    await broker.declare_exchange(exchange_catalogs)
    await broker.declare_exchange(exchange_orders)
