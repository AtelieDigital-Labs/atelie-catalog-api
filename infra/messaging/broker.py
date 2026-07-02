from faststream.rabbit import RabbitBroker
from faststream import FastStream

from app.core.config import settings

broker = RabbitBroker(settings.MESSAGING_URL)
from .handlers.stock_reservation import stock_reservation_handler
from .handlers.stock_expire import stock_expire_handler
from .handlers.stock_confirm import stock_confirm_handler