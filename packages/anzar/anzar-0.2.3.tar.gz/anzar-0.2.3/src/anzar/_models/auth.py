from pydantic import BaseModel, EmailStr

from .user import User


class EmailRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class SuccessResponse(BaseModel):
    message: str


class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: User


class JWTTokens(BaseModel):
    accessToken: str
    refreshToken: str
    refreshTokenJti: str | None = None
