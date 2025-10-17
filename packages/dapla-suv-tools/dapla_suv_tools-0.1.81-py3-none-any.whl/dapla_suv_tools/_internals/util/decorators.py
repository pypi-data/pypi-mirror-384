from typing import Callable
from functools import wraps

from dapla_suv_tools._internals.util.operation_result import OperationResult


def result_to_dict(func) -> Callable[..., dict]:
    @wraps(func)
    def inner(self, *args, **kwargs) -> dict:
        try:
            result = func(self, *args, **kwargs)
            if isinstance(result, OperationResult):
                return result.process(caller=self)
            return result
        except Exception as e:
            if hasattr(self, "suppress_exceptions") and self.suppress_exceptions:
                return {
                    "result": "An unexpected error occurred",
                    "error": str(e)
                }
            raise e
    return inner


def refresh_token_cache(func):
    @wraps(func)
    def inner(*args, **kwargs):
        args[0].refresh_token()
        return func(*args, **kwargs)

    return inner
