from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    message: str


class AddressSchema(BaseModel):
    street: str = Field(max_length=255)
    number: int = Field(gt=0)
    neighborhood: str = Field(max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(max_length=9)
    complement: Optional[str] = Field(default=None, max_length=255)


class AddressPublic(AddressSchema):
    id: int

    class ConfigDict:
        from_attributes = True


class CategorySchema(BaseModel):
    name: str = Field(min_length=3, max_length=150)


class CategoryPublic(CategorySchema):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CategoryList(BaseModel):
    categories: list[CategoryPublic]


class StoreSchema(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category_id: int = Field(description='ID da categoria pré-existente')
    image: str | None = Field(default=None, max_length=255)
    banner: str | None = Field(default=None, max_length=255)
    address: AddressSchema


class StorePublic(BaseModel):
    id: int
    artisan_id: str
    name: str
    description: str | None
    category: CategoryPublic
    image: str | None = None
    banner: str | None = None

    address: Optional[AddressPublic] = None
    created_at: datetime
    updated_at: datetime

    class ConfigDict:
        from_attributes = True


class StoreList(BaseModel):
    stores: list[StorePublic]


class CategoryUpdate(BaseModel):
    name: Optional[str] = None


class AddressUpdate(BaseModel):
    street: Optional[str] = Field(default=None, max_length=255)
    number: Optional[int] = Field(default=None, gt=0)
    neighborhood: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(default=None, max_length=9)
    complement: Optional[str] = Field(default=None, max_length=255)


class StoreUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=500)
    image: Optional[str] = Field(default=None, max_length=255)
    banner: Optional[str] = Field(default=None, max_length=255)
    address: Optional[AddressUpdate] = None


class FilterPage(BaseModel):
    offset: int = Field(ge=0, default=0)
    limit: int = Field(gt=0, default=10)


class FilterStore(FilterPage):
    name: str | None = Field(default=None, min_length=3)
    category_id: int | None = Field(default=None)
