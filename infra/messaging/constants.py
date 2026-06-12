from enum import StrEnum

class Exchange(StrEnum):
    ACCOUNTS_EXCHANGE = "accounts.events"
    ORDER_EXCHANGE = "orders.events"
    CATALOG_EXCHANGE = "catalogs.events"

class Queue(StrEnum):
    USER_CREATED_QUEUE = "accounts.user.created.queue"
    WALLET_TRANSACTION_QUEUE = 'accounts.wallet.transaction.queue'
    BECOME_ARTISAN_QUEUE= "accounts.become.artisan.queue"
    CREATE_WALLET_QUEUE= "accounts.create.wallet.queue"

class RoutingKey(StrEnum):
    USER_CREATED_ROUTING_KEY = "accounts.user.created"
    ORDER_PAID_ROUTING_KEY = "orders.order.paid"
    STORE_CREATED_ROUTING_KEY = "catalogs.store.created"