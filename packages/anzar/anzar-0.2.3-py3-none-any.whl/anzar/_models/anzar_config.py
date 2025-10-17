from enum import Enum
from pydantic import BaseModel


class DatabaseDriver(str, Enum):
    SQLite = "SQLite"
    PostgreSQL = "PostgreSQL"
    MongoDB = "MongoDB"


class Database(BaseModel):
    connection_string: str
    driver: DatabaseDriver


class AuthStrategy(str, Enum):
    Jwt = "Jwt"
    Session = "Session"


class Authentication(BaseModel):
    strategy: AuthStrategy
    # expires_in: str


class EmailAndPassword(BaseModel):
    enable: bool


class HttpsConfig(BaseModel):
    enabled: bool
    cert_path: str | None = None
    key_path: str | None = None
    port: int | None = None


class AnzarConfig(BaseModel):
    api_url: str
    database: Database
    auth: Authentication
    emailAndPassword: EmailAndPassword = EmailAndPassword(enable=True)
    https: HttpsConfig
