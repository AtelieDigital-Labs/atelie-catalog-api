from faststream.rabbit import RabbitBroker
from faststream import FastStream
broker = RabbitBroker("amqp://guest:guest@rabbitmq:5672/")
app = FastStream(broker)
from .handlers.stock_reservation import stock_reservation_handler
from .handlers.stock_expire import stock_expire_handler
from .handlers.stock_confirm import stock_confirm_handler

