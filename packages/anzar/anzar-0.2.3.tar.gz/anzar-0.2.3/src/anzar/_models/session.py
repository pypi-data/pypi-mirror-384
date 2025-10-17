from pydantic import BaseModel


class Session(BaseModel):
    # id: str | None = Field(None, alias="_id")
    _id: str | None
    userId: str
    createdAt: str
    expiresAt: str
    updatedAt: str
    token: str
