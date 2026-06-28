from dataclasses import dataclass
from decimal import Decimal

@dataclass
class OrderItemEvent:
    product_variant_id: str
    quantity: int

@dataclass
class OrderPaidEvent:
    order_id: str
    customer_id: str
    store_id: str
    artisan_id: str
    total_amount: Decimal
    items: list[OrderItemEvent]