from pydantic import BaseModel


class Error(BaseModel):
    message: str

    @classmethod
    def server_down(cls) -> "Error":
        return cls(
            message="The server is currently unavailable. Please check the server status or try again later."
        )

    @classmethod
    def internal_error(cls) -> "Error":
        return cls(message="Something went wrong.")
