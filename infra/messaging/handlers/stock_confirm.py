from app.core.database import get_session
from app.services.product import ProductService
from ..broker import broker
from ..exchanges import exchange_orders
from ..queues import product_reservation_confirm_queue
from sqlalchemy.ext.asyncio import AsyncSession
from fast_depends import Depends
from ..events.order_paid import OrderPaidEvent


@broker.subscriber(
    exchange=exchange_orders,
    queue=product_reservation_confirm_queue
)
async def stock_confirm_handler(
    data: OrderPaidEvent,
    session: AsyncSession = Depends(get_session),
):
    await ProductService.confirm_reserve(
        session=session,
        data=data,
    )