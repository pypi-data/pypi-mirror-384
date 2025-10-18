from anzar._utils.types import Header, Token, TokenType


class Config:
    def headers(self, token: Token | None, context_id: str) -> Header:
        # header: Content-Type: application/x-www-form-urlencoded
        default_headers = {
            "X-Context-ID": context_id,
            "Content-Type": "application/json",
            "User-Agent": "Anzar-SDK/1.0",
        }
        if token is not None:
            if token.tokenType == TokenType.AccessToken:
                default_headers["authorization"] = f"Bearer {token.value}"
            if token.tokenType == TokenType.RefreshToken:
                default_headers["x-refresh-token"] = f"Bearer {token.value}"

        return default_headers
