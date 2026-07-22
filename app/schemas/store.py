from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends, Form, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductPublic


class Message(BaseModel):
    message: str


class AddressSchema(BaseModel):
    street: str = Field(max_length=255)
    number: int = Field(gt=0, examples=[29])
    neighborhood: str = Field(max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(max_length=9)
    complement: Optional[str] = Field(default=None, max_length=255)

    @classmethod
    def as_form(
        cls,
        street: str = Form(),
        number: int = Form(exemple=20),
        city: str = Form(...),
        state: str = Form(examples=["RN"]),
        zip_code: str = Form(examples=["00000-000"]),
        neighborhood: str = Form(...)

    ):
        return cls(
                street=street,
                number=number,
                neighborhood=neighborhood,
                city=city,
                state=state,
                zip_code=zip_code,
        )


class AddressPublic(AddressSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


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
    address: AddressSchema

    pix_key: str = Field(
        max_length=150,
    )

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: str | None = Form(None),
        category_id: int = Form(...),
        pix_key: str = Form(examples=['artesao@email.com']),
        address: AddressSchema = Depends(AddressSchema.as_form),
    ):
        return cls(
            name=name,
            description=description,
            category_id=category_id,
            pix_key=pix_key,
            address=address,
        )


class StoreSchemaPrivate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category_id: int = Field(description='ID da categoria pré-existente')
    image: str | None = Field(default=None, max_length=255)
    banner: str | None = Field(default=None, max_length=255)
    address: AddressSchema

    pix_key: str = Field(
        max_length=150,
    )


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

    model_config = ConfigDict(from_attributes=True)


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

    @classmethod
    def as_form(
        cls,
        street: Annotated[str | None, Form()] = None,
        number: Annotated[int | None, Form()] = None,
        city: Annotated[str | None, Form()] = None,
        state: Annotated[str | None, Form(examples=["RN"])] =  None,
        zip_code: Annotated[str | None, Form(examples=["00000-000"])] = None,
        neighborhood: Annotated[str | None, Form()] = None

    ):
        return cls(
                street=street,
                number=number,
                neighborhood=neighborhood,
                city=city,
                state=state,
                zip_code=zip_code,
        )


class StoreUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    address: AddressUpdate | None = None

    @classmethod
    def as_form(
        cls,
        description: Annotated[str | None, Form()] = None,
        address: Annotated[AddressUpdate | None, Depends(AddressUpdate.as_form)] = None,
    ) -> "StoreUpdate":
        return cls(
            description=description,
            address=address,
        )

class StoreUpdatePrivate(BaseModel):
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


class StoreWithProductsPublic(BaseModel):
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
    products: list[ProductPublic] = []

    model_config = ConfigDict(from_attributes=True)


class MyStoreList(BaseModel):
    stores: list[StorePublic]


class StoreArtisanPublic(BaseModel):
    store_id: int
    artisan_id: str
