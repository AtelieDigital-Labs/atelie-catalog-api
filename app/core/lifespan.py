from infra.messaging.broker import broker
from infra.messaging.exchanges import declare_exchange
from contextlib import asynccontextmanager
from fastapi import FastAPI
from infra.messaging.queues import product_reservation_ttl_queue
import asyncio
from infra.messaging.worker import process_outbox_messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Conectando ao RabbitMQ e criando estruturas...")
    await broker.connect() 
    await broker.start()
    await declare_exchange(broker=broker)
    await broker.declare_queue(product_reservation_ttl_queue)

    print("Iniciando o worker de polling do Outbox...")

    poller_task = asyncio.create_task(process_outbox_messages())

    try:
        yield  
    finally:
        print("Realizando encerramento para o worker do Outbox...")

        poller_task.cancel()
        
        try:
            await poller_task
        except asyncio.CancelledError:
            pass

        print("Desconectando do RabbitMQ...")
        await broker.stop()