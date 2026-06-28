from pydantic import BaseModel, Field


class OrderCreatedEvent(BaseModel):
    order_id : int
    product_variant_id: int
    quantity: int = Field(gt=0)