from infra.messaging.broker import broker
from infra.messaging.exchanges import declare_exchange
from contextlib import asynccontextmanager
from fastapi import FastAPI
from infra.messaging.queues import product_reservation_ttl_queue

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Conectando ao RabbitMQ e criando estruturas...")
    await broker.connect() 
    await broker.start()
    await declare_exchange(broker=broker)
    await broker.declare_queue(product_reservation_ttl_queue)
    try:
        yield  # Aqui a API fica rodando e aceitando requisições HTTP
    finally:
        print("Desconectando do RabbitMQ...")
        await broker.stop()