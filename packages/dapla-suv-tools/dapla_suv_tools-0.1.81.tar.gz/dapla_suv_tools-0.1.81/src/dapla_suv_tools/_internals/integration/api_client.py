import inspect

import requests

from dapla_suv_tools._internals.integration import user_tools
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants


class SuvApiClient:
    base_url: str

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, path: str, context: SuvOperationContext) -> str:
        headers = self._get_headers(context)

        response = requests.get(f"{self.base_url}{path}", headers=headers)

        return self._handle_response(response=response, context=context)

    def post(self, path: str, body_json: str, context: SuvOperationContext) -> str:
        headers = self._get_headers(context)

        response = requests.post(
            url=f"{self.base_url}{path}", headers=headers, data=body_json
        )

        return self._handle_response(response=response, context=context)

    def post_json(self, path: str, body_json: str, context: SuvOperationContext) -> str:
        headers = self._get_headers(context)

        response = requests.post(
            url=f"{self.base_url}{path}", headers=headers, json=body_json
        )

        return self._handle_response(response=response, context=context)

    def put(self, path: str, body_json: str, context: SuvOperationContext) -> str:
        headers = self._get_headers(context)
        response = requests.put(
            url=f"{self.base_url}{path}", headers=headers, data=body_json
        )
        return self._handle_response(response=response, context=context)

    def delete(self, path: str, context: SuvOperationContext) -> str:
        headers = self._get_headers(context)

        response = requests.delete(url=f"{self.base_url}{path}", headers=headers)

        return self._handle_response(response, context=context)

    def _handle_response(
        self, response: requests.Response, context: SuvOperationContext
    ) -> str:
        called = self._get_caller(2)
        caller = self._get_caller(3)

        msg = f"calling '{called}' from '{caller}'."

        if not self._success(response.status_code):
            error = response.content.decode("UTF-8")
            ex = Exception(f"Failed call to api while {msg}.")
            context.set_error(
                f"Error (status: {response.status_code}) {msg}:  {error}", ex
            )
            raise ex

        context.log(level=constants.LOG_DIAGNOSTIC, operation=called, message=msg)

        return response.content.decode("UTF-8")

    @staticmethod
    def _get_headers(context: SuvOperationContext) -> dict:
        token: str = user_tools.get_access_token(context)

        return {"authorization": f"Bearer {token}", "content-type": "application/json"}

    @staticmethod
    def _get_caller(depth: int) -> str:
        frames = inspect.stack()
        caller = frames[depth]
        return caller.function

    @staticmethod
    def _success(status_code: int) -> bool:
        return str(status_code).startswith("2")
