import requests


class HttpInterceptor(requests.Session):
    def __init__(self) -> None:
        super().__init__()
