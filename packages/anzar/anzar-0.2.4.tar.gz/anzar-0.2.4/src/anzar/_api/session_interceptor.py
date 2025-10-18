from typing import Any, override
import requests
from anzar._api.http_interceptor import HttpInterceptor
from anzar._models.anzar_config import AnzarConfig
from anzar.core.config import Config
from anzar._utils.context import Context
from anzar._utils.storage import TokenStorage
from anzar._utils.types import TokenType


class SessionInterceptor(HttpInterceptor):
    def __init__(self, config: AnzarConfig) -> None:
        super().__init__()
        self.verify = config.https.cert_path
        self.API_URL: str = config.api_url
        self.storage: TokenStorage = TokenStorage()
        self.ctx: Context = Context()

    @override
    def request(
        self,
        method: str | bytes,
        url: str | bytes,
        _refresh_attempted: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> requests.Response:
        session_id = self.storage.load(TokenType.SessionToken.name)
        if session_id:
            _ = self.cookies.set("id", session_id)

        context_id = self.ctx.load()
        kwargs["headers"] = Config().headers(
            token=None, context_id=context_id if context_id else ""
        )

        response = super().request(method, url, timeout=30, *args, **kwargs)

        if url == f"{self.API_URL}/auth/logout":
            self.storage.clear(TokenType.SessionToken.name)
            return response

        if sessionID := dict(response.cookies).get("id"):
            self.storage.save(TokenType.SessionToken, sessionID)

        return response
