from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class Message(BaseModel):
  message: str 

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
   category_id: int | None = Field(default=None)

class StorePublic(StoreSchema):
    id: int
    image: str | None = None
    banner: str | None = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class StoreList(BaseModel):
    stores: list[StorePublic]

class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    category_id: int | None = Field(default=None)
    image: str | None = Field(default=None, max_length=255)
    banner: str | None = Field(default=None, max_length=255)


# para filtros de paginação 
class FilterPage(BaseModel):
    offset: int = Field(ge=0, default=0)
    limit: int = Field(gt=0, default=10)

class FilterStore(FilterPage):
    name: str | None = Field(default=None, min_length=3)
    category_id: int | None = Field(default=None)