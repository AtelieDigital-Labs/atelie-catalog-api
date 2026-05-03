from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ProductImageSchema(BaseModel):
    url: str = Field(
        max_length=255,
        examples=['meu-bucket.s3.atelie.com/foto.jpg'],
    )
    is_primary: bool = Field(
        default=False,
        examples=[True],
    )


class ProductImagePublic(BaseModel):
    id: int
    url: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class ProductVariationSchema(BaseModel):
    price: Decimal = Field(gt=0, examples=[89.90])
    weight: float = Field(gt=0, examples=[0.3])
    length: float = Field(gt=0, examples=[30.0])
    width: float = Field(gt=0, examples=[20.0])
    height: float = Field(gt=0, examples=[2.0])

    sku: Optional[str] = Field(
        default=None,
        max_length=50,
        examples=['CAM-001-M-BRANCO'],
    )
    stock: int = Field(ge=0, default=0, examples=[10])

    color: Optional[str] = Field(
        default=None,
        max_length=50,
        examples=['Branco'],
    )
    size: Optional[str] = Field(
        default=None,
        max_length=50,
        examples=['M'],
    )

    images: List[ProductImageSchema] = Field(
        default=[],
        examples=[
            [
                {
                    'url': 'https://meu-bucket.s3.amazonaws.com/foto.jpg',
                    'is_primary': True,
                }
            ]
        ],
    )


class ProductVariationPublic(BaseModel):
    id: int
    price: Decimal
    weight: float
    length: float
    width: float
    height: float
    sku: Optional[str] = None
    stock: int
    color: Optional[str] = None
    size: Optional[str] = None
    images: List[ProductImagePublic]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('price')
    @staticmethod
    def serialize_price(value: Decimal):
        return float(value)


class ProductSchema(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=100,
        examples=['Camiseta Artesanal'],
    )
    description: str = Field(
        max_length=255,
        examples=['Camiseta feita à mão com tecido natural'],
    )
    store_id: int = Field(examples=[1])

    variations: List[ProductVariationSchema]


class ProductPublic(BaseModel):
    id: int
    name: str
    description: str
    store_id: int
    is_active: bool

    variations: List[ProductVariationPublic]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    products: List[ProductPublic]


class ImageUpdate(BaseModel):
    id: Optional[int] = None
    url: str
    is_primary: bool = False


class VariationUpdate(BaseModel):
    id: Optional[int] = None
    price: float
    weight: float
    length: float
    width: float
    height: float
    stock: int
    sku: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    images: List[ImageUpdate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    variations: Optional[List[VariationUpdate]] = None


class FilterProduct(BaseModel):
    offset: int = Field(ge=0, default=0)
    limit: int = Field(gt=0, default=10)

    name: Optional[str] = Field(default=None, min_length=3)
    store_id: Optional[int] = None
