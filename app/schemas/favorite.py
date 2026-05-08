from pydantic import BaseModel, ConfigDict


class FavoritePublic(BaseModel):
    id: int
    user_id: str
    product_id: int

    model_config = ConfigDict(from_attributes=True)


class FavoriteList(BaseModel):
    favorites: list[FavoritePublic]