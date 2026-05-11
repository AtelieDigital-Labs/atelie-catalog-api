from pydantic import BaseModel, ConfigDict, Field


class ReviewSchema(BaseModel):
    rating: int = Field(ge=1, le=5, examples=[5])
    comment: str | None = Field(
        default=None,
        max_length=500,
        examples=['Produto excelente, superou minhas expectativas!'],
    )


class ReviewPublic(BaseModel):
    id: int
    user_id: str
    product_id: int
    rating: int
    comment: str | None

    model_config = ConfigDict(from_attributes=True)


class ReviewList(BaseModel):
    reviews: list[ReviewPublic]
    total: int
    average_rating: float


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)