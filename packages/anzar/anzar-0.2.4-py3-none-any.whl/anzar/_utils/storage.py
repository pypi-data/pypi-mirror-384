import keyring

from anzar._utils.types import TokenType


SERVICE_NAME = "AnzarSDK"

ACCESS_TOKEN = TokenType.AccessToken.name
REFRESH_TOKEN = TokenType.RefreshToken.name
SESSION_TOKEN = TokenType.SessionToken.name


class TokenStorage:
    def save(self, token_type: TokenType, token: str):
        try:
            keyring.set_password(SERVICE_NAME, token_type.name, token)
        except Exception as e:
            print(e)

    def load(self, username: str):
        try:
            return keyring.get_password(SERVICE_NAME, username)
        except Exception as e:
            print(e)

    def clear(self, username: str):
        try:
            keyring.delete_password(SERVICE_NAME, username)
        except Exception as e:
            print(e)
