import asyncio
from app.core.database import get_session
from app.repositories.outbox import OutboxRepository
from infra.messaging.publishers.log_register import publisher_log_register
from app.core.logger import setup_trigger_logger
 
trigger_logger = setup_trigger_logger()

async def process_outbox_messages():

    await asyncio.sleep(3)

    while True:
        try:
            async for session in get_session():
                logs = await OutboxRepository.get_log(session=session)

                if logs:
                    for log in logs:
                        try:
                            await publisher_log_register(message=log.payload)

                            log.processed = True
                            
                            trigger_logger.info(f"Log {log.log_id} enviado para a mensageria com sucesso")
                        except Exception as e:
                            trigger_logger.error(f"Erro ao publicar o log {log.log_id}: {e}")

                            break
                    await session.commit()
                
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            trigger_logger.info("Worker do Outbox finalizado com segurança.")
            break
            
        except Exception as e:
            trigger_logger.error(f"Erro no worker de polling do outbox: {e}")
            await asyncio.sleep(5) 