import dotenv
import yaml

from anzar._api.jwt_interceptor import JwtInterceptor
from anzar._api.session_interceptor import SessionInterceptor
from anzar._api.authenticator import AuthManager
from anzar._models.anzar_config import (
    AnzarConfig,
    AuthStrategy,
    Authentication,
    Database,
    HttpsConfig,
)

from ._api.client import HttpClient

_ = dotenv.load_dotenv()


def load_config(path: str) -> AnzarConfig:
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return AnzarConfig(
            api_url=data["api_url"],
            database=Database(**data["database"]),
            auth=Authentication(**data["auth"]),
            https=HttpsConfig(**data["https"]),
        )
    except Exception as e:
        print(e)
        import sys

        sys.exit("check you configuration file: anzar.yml")


def AnzarAuth() -> AuthManager:
    config = load_config("anzar.yml")

    http_interceptor = (
        SessionInterceptor(config)
        if config.auth.strategy == AuthStrategy.Session
        else JwtInterceptor(config)
    )

    return AuthManager(
        HttpClient(http_interceptor),
        config,
    )


__all__ = ["AnzarAuth"]
