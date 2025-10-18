from pydantic import BaseModel


class Session(BaseModel):
    # id: str | None = Field(None, alias="_id")
    _id: str | None
    userId: str
    issuedAt: str
    expiresAt: str
    usedAt: str
    token: str
