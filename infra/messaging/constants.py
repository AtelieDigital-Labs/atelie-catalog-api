from enum import StrEnum

class Exchange(StrEnum):
    ACCOUNTS_EXCHANGE = "accounts.events"
    ORDER_EXCHANGE = "orders.events"
    CATALOG_EXCHANGE = "catalogs.events"
    DQL_EXCHANGE = "dql.evenvts"
    LOG_EXCHANGE = "logs.events"


class Queue(StrEnum):
    USER_CREATED_QUEUE = "accounts.user.created.queue"
    WALLET_TRANSACTION_QUEUE = 'accounts.wallet.transaction.queue'
    BECOME_ARTISAN_QUEUE= "accounts.become.artisan.queue"
    CREATE_WALLET_QUEUE= "accounts.create.wallet.queue"
    STOCK_RESERVATION_QUEUE = "catalogs.stock.reservation.queue"
    STOCK_RESERVATION_TTL_QUEUE = "catalogs.stock.reservation.ttl.queue"
    STOCK_RESERVATION_CONFIRM_QUEUE = "catalogs.stock.reservation.confirm.queue"
    PRODUCT_RESERVATION_EXPIRE_DLQ = "catalogs.product.reservation.expire.dlq"

class RoutingKey(StrEnum):
    USER_CREATED_ROUTING_KEY = "accounts.user.created"
    ORDER_PAID_ROUTING_KEY = "orders.order.paid"
    ORDER_CREATED_ROUTING_KEY = "orders.order.created"
    STORE_CREATED_ROUTING_KEY = "catalogs.store.created"
    STOCK_RESERVATION_EXPIRE_ROUTING_KEY = "catalogs.stock.reservation.expire"
    LOG_REGISTER_ROUTING_KEY = "logs.register"