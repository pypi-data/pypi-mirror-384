from anzar._api.client import HttpClient
from anzar._models.anzar_config import AnzarConfig, AuthStrategy
from anzar._models.auth import AuthResponse, SuccessResponse
from anzar._models.session import Session
from anzar._models.user import User

from anzar._utils.errors import Error
from anzar._utils.storage import TokenStorage
from anzar._utils.types import NoType, TokenType
from anzar._utils.validator import Validator


class AuthManager:
    def __init__(self, httpClient: HttpClient, config: AnzarConfig) -> None:
        self._http_client: HttpClient = httpClient
        self.config: AnzarConfig = config

        self.__endpoints: dict[str, str] = {
            "health_check": f"{self.config.api_url}/health_check",
            "login": f"{self.config.api_url}/auth/login",
            "register": f"{self.config.api_url}/auth/register",
            "session": f"{self.config.api_url}/auth/session",
            "user": f"{self.config.api_url}/user",
            "logout": f"{self.config.api_url}/auth/logout",
            "forgot-password": f"{self.config.api_url}/auth/password/forgot",
        }

        _ = self._http_client.get(self.__endpoints["health_check"], NoType)

    def register(self, username: str, email: str, password: str) -> Error | User:
        req = Validator().construct_register(username, email, password)
        if isinstance(req, Error):
            return req

        url = self.__endpoints["register"]
        response = self._http_client.post(url, req, AuthResponse)

        return response.user if isinstance(response, AuthResponse) else response

    def login(self, email: str, password: str):
        req = Validator().construct_login(email, password)
        if isinstance(req, Error):
            return req

        url = self.__endpoints["login"]
        response = self._http_client.post(url, req, AuthResponse)

        return response.user if isinstance(response, AuthResponse) else response

    def logout(self):
        url = self.__endpoints["logout"]
        response = self._http_client.post(url, None, NoType)

        return response

    def getSession(self):
        user_response = self._http_client.get(self.__endpoints["user"], User)
        if isinstance(user_response, Error):
            return user_response

        session_response = self._http_client.get(self.__endpoints["session"], Session)
        if isinstance(session_response, Error):
            return session_response

        return {"session": session_response, "user": user_response}

    def isLoggedIn(self):
        match self.config.auth.strategy:
            case AuthStrategy.Session:
                return TokenStorage().load(TokenType.SessionToken.name) is not None
            case AuthStrategy.Jwt:
                return TokenStorage().load(TokenType.AccessToken.name) is not None

    def reset_password(self, email: str):
        req = Validator().construct_email(email)
        if isinstance(req, Error):
            return req

        url = self.__endpoints["forgot-password"]
        response = self._http_client.post(url, req, SuccessResponse)
        return response
