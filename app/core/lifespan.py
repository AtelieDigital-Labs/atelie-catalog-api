from infra.messaging.broker import broker
from infra.messaging.exchanges import declare_exchange
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Conectando ao RabbitMQ e criando estruturas...")
    await broker.connect() 
    await declare_exchange(broker=broker)
    try:
        yield  # Aqui a API fica rodando e aceitando requisições HTTP
    finally:
        print("Desconectando do RabbitMQ...")
        await broker.close()