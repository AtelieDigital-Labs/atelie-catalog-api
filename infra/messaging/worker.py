import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.local"
)

django.setup()

from infra.messaging.base_consumer import RabbitMQConsumer


from infra.messaging.constants import *

from apps.wallets.messaging.handlers.order_paid import callback_wallet_transaction


from apps.wallets.messaging.handlers.store_created import (
    callback_store_created
)


consumer = RabbitMQConsumer()

consumer.register(
    exchange=ORDER_EXCHANGE,
    queue=WALLET_TRANSACTION_QUEUE,
    routing_key=ORDER_PAID_ROUTING_KEY,
    callback=callback_wallet_transaction,
)

consumer.register(
    exchange=STORE_EXCHANGE,
    queue=STORE_CREATED_QUEUE,
    routing_key=STORE_CREATED_ROUTING_KEY,
    callback=callback_store_created,
)

consumer.start()