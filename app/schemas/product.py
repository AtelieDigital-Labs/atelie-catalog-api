from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ProductImageSchema(BaseModel):
    url: str = Field(max_length=255)
    is_primary: bool = False


class ProductImagePublic(ProductImageSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProductVariationSchema(BaseModel):
    price: Decimal = Field(gt=0)
    weight: float = Field(gt=0)
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

    sku: Optional[str] = Field(default=None, max_length=50)
    stock: int = Field(ge=0, default=0)

    color: Optional[str] = Field(default=None, max_length=50)
    size: Optional[str] = Field(default=None, max_length=50)

    images: List[ProductImageSchema] = []



class ProductVariationPublic(ProductVariationSchema):
    id: int
    images: List[ProductImagePublic]

    model_config = ConfigDict(from_attributes=True)


class ProductSchema(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(max_length=255)
    store_id: int

    variations: List[ProductVariationSchema]

class ProductPublic(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool

    variations: List[ProductVariationPublic]

    model_config = ConfigDict(from_attributes=True)

class ProductList(BaseModel):
    products: List[ProductPublic]

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class FilterProduct(BaseModel):
    offset: int = Field(ge=0, default=0)
    limit: int = Field(gt=0, default=10)

    name: Optional[str] = Field(default=None, min_length=3)
    store_id: Optional[int] = None