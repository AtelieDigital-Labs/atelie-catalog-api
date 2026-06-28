from pydantic import BaseModel, Field

class StockReservedEvent(BaseModel):
    reserve_id: int
    order_id: int
    product_variant_id: int
    quantity: int = Field(gt=0)
