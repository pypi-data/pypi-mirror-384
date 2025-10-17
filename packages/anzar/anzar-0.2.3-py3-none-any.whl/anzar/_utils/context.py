import keyring
from pydantic import BaseModel


class ContextModel(BaseModel):
    context_id: str


SERVICE_NAME = "AnzarSDK"
USERNAME = "Context"


class Context:
    def save(self, context_id: str):
        try:
            keyring.set_password(SERVICE_NAME, USERNAME, context_id)
        except Exception as e:
            print(e)

    def load(self):
        try:
            return keyring.get_password(SERVICE_NAME, USERNAME)
        except Exception as e:
            print(e)

    def clear(self):
        keyring.delete_password(SERVICE_NAME, USERNAME)
