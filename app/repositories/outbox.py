from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.outbox import LogOutbox

class OutboxRepository:
    @staticmethod
    async def get_log(session: AsyncSession):
        stmt = select(LogOutbox).where(LogOutbox.processed == False).order_by(LogOutbox.created_at).limit(50)

        result = await session.execute(stmt)
        logs = result.scalars(result).all()

        return logs 