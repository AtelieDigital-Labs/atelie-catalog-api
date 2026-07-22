from ..broker import broker
from ..exchanges import exchange_dlq
from ..queues import product_reservation_dlq
from app.services.product import ProductService
from fast_depends import Depends
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..events.stock_reserved import StockReservedEvent

@broker.subscriber(
    exchange=exchange_dlq,
    queue=product_reservation_dlq
)
async def stock_expire_handler(
    data: StockReservedEvent,
    session: AsyncSession = Depends(get_session),
):
    await ProductService.expire_reserve(
        session=session,
        data=data,
    )