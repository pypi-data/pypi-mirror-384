# pyright: reportExplicitAny=false
# pyright: reportAny=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false

from typing import Any, override

import requests
# from requests.adapters import HTTPAdapter
# from urllib3.util import Retry

from anzar._api.http_interceptor import HttpInterceptor
from anzar._models.anzar_config import AnzarConfig
from anzar._models.auth import AuthResponse
from anzar.core.config import Config
from anzar._utils.context import Context
from anzar.core.logger import logger
from anzar._utils.storage import TokenStorage
from anzar._utils.types import Token, TokenType


class JwtInterceptor(HttpInterceptor):
    def __init__(self, config: AnzarConfig) -> None:
        super().__init__()
        self.verify = config.https.cert_path
        self.API_URL: str = config.api_url
        self.ctx: Context = Context()
        self.storage: TokenStorage = TokenStorage()

        self.endpoint_config: dict[str, TokenType | None] = {
            f"{self.API_URL}/auth/login": None,
            f"{self.API_URL}/auth/register": None,
            f"{self.API_URL}/auth/refreshToken": TokenType.RefreshToken,
            f"{self.API_URL}/auth/logout": TokenType.RefreshToken,
        }

        # Retry logic (optional)
        # retries = Retry(
        #     total=3,
        #     backoff_factor=1,
        #     status_forcelist=[500, 502, 503, 504],
        #     allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        # )
        # adapter = HTTPAdapter(max_retries=retries)
        # self.mount("http://", adapter)
        # self.mount("https://", adapter)

    def __extractTokenFromCache(self, tokenType: TokenType) -> Token | None:
        token = self.storage.load(tokenType.name)
        return Token.new(token, tokenType) if token else None

    def __pre_request(self, url: str, **kwargs) -> dict[str, str]:
        token_type = self.endpoint_config.get(url, TokenType.AccessToken)
        token = self.__extractTokenFromCache(token_type) if token_type else None

        context_id = self.ctx.load()
        kwargs["headers"] = Config().headers(
            token=token, context_id=context_id if context_id else ""
        )

        return kwargs

    def __post_response(self, url: str, response: requests.Response):
        if not response.ok:
            return

        # HACK
        if url == f"{self.API_URL}/auth/logout":
            self.storage.clear(TokenType.AccessToken.name)
            self.storage.clear(TokenType.RefreshToken.name)
            return

        token_type = self.endpoint_config.get(url, TokenType.AccessToken)
        if token_type == TokenType.AccessToken:
            return

        auth_response = AuthResponse.model_validate(response.json())
        self.storage.save(TokenType.AccessToken, auth_response.accessToken)
        self.storage.save(TokenType.RefreshToken, auth_response.refreshToken)

    @override
    def request(
        self,
        method: str | bytes,
        url: str,
        _refresh_attempted: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> requests.Response:
        logger.info(f"{method} {url}")

        kwargs = self.__pre_request(url, **kwargs)
        response = super().request(method, url, timeout=30, *args, **kwargs)

        logger.info(f"Response: {response.status_code}")

        token_type = self.endpoint_config.get(url, TokenType.AccessToken)
        if (
            response.status_code == 401
            and token_type == TokenType.AccessToken
            and not _refresh_attempted
        ):
            # HACK
            # don't use recursion
            # instead use: response = super().request("POST", "auth/refreshToken", timeout=30, *args, **kwargs)
            response = self.request(
                method="POST",
                url=f"{self.API_URL}/auth/refreshToken",
                _refresh_attempted=True,
                *args,
                **kwargs,
            )

            # NOTE res-execute previous request
            kwargs = self.__pre_request(url, **kwargs)
            response = super().request(method, url, timeout=30, *args, **kwargs)

        self.__post_response(url, response)
        return response
