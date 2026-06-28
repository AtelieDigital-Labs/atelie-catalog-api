from ..broker import broker
from ..exchanges import exchange_orders
from app.services.product import ProductService
from ..events.order_create import OrderCreatedEvent
from ..events.stock_reserved import StockReservedEvent
from fast_depends import Depends
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from ..queues import product_reservation_queue, product_reservation_ttl_queue


@broker.subscriber(
    exchange=exchange_orders,
    queue=product_reservation_queue
)
async def stock_reservation_handler(
    data: OrderCreatedEvent,
    session: AsyncSession = Depends(get_session)
):
    reserve = await ProductService.reserve(
        session=session,
        data=data
    )
    
    return await broker.publish(
        StockReservedEvent(
            reserve_id=reserve.id,
            order_id=reserve.order_id,
            product_variant_id=reserve.product_variant_id,
            quantity=reserve.quantity,
        ),
        queue=product_reservation_ttl_queue.name,
    )