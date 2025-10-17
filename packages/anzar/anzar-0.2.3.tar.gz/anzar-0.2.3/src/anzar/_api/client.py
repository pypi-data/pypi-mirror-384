import sys
from pydantic import BaseModel
from requests.models import Response
from requests.exceptions import ConnectionError


from anzar._api.http_interceptor import HttpInterceptor
from anzar._utils.errors import Error
from anzar._utils.validator import Validator


class HttpClient:
    def __init__(self, http_interceptor: HttpInterceptor):
        self.http_interceptor: HttpInterceptor = http_interceptor
        self.accessToken: str | None = None

    def get[T: BaseModel](self, url: str, model_type: type[T]) -> T | Error:
        try:
            response: Response = self.http_interceptor.get(url)

            if response.status_code in (200, 201):
                return model_type.model_validate(response.json())

            return Error.model_validate(response.json())
        except ConnectionError:
            sys.exit(Error.server_down().message)
        except Exception as e:
            print(e)
            return Error.internal_error()

    def post[T: BaseModel](
        self, url: str, data: BaseModel | None, model_type: type[T]
    ) -> T | Error:
        try:
            payload = data.model_dump() if data else None
            response: Response = self.http_interceptor.post(url, json=payload)

            if response.status_code in (200, 201):
                return Validator().validate(model_type, response)

            return Error.model_validate(response.json())
        except ConnectionError:
            sys.exit(Error.server_down().message)
        except Exception as e:
            print(e)
            return Error.internal_error()
