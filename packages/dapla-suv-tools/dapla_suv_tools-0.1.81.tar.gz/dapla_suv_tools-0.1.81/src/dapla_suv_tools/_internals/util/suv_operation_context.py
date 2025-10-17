from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional
import inspect

from dapla_suv_tools._internals.util import constants


class SuvOperationContext:
    state: dict[str, Any]
    func_args: Optional[tuple]
    func_kwargs: Optional[dict[str, Any]]
    arg_validator: Optional[Callable[["SuvOperationContext", dict], None]]

    def __init__(
        self,
        validator: Optional[Callable[["SuvOperationContext", dict], None]] = None,
        func_kwargs: Optional[dict[str, Any]] = None,
    ):
        self.arg_validator = validator
        self._flush_state()
        self.func_kwargs = func_kwargs

    def __enter__(self):
        self._flush_state()
        try:
            if self.func_kwargs and self.arg_validator:
                self.arg_validator(self, self.func_kwargs)

            return self
        except Exception as e:
            self.__exit__(type(e), e, e.__traceback__)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            if self.state["errors"]:
                print("Errors flagged during operation:")
                for error in self.state["errors"]:
                    print(error)
            return False
        return True

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.log(
                level=constants.LOG_DIAGNOSTIC,
                operation=func.__name__,
                message=f"Starting function call '{func.__name__}'",
                result="N/A",
            )
            if self.arg_validator is not None:
                self.arg_validator(self, kwargs)
            self.func_args = args
            self.func_kwargs = kwargs
            with self._recreate_context_manager():
                sig = inspect.signature(func)
                if "context" in sig.parameters or "kwargs" in sig.parameters:
                    return func(*args, **kwargs, context=self)
                return func(*args, **kwargs)

        return wrapper

    def _recreate_context_manager(self):
        return self

    def log(
        self,
        *,
        level: str = constants.LOG_INFO,
        operation: str | None = None,
        message: str = "",
        result: str = "OK",
    ):
        now = datetime.now()
        if operation is None:
            frames = inspect.stack()
            operation = frames[1].function

        self.state["log"].append(
            {
                "level": level,
                "time": str(now),
                "operation": operation,
                "message": message,
                "result": result,
            }
        )

    def set_error(self, error_msg: str, exception: Exception):
        frames = inspect.stack()
        operation = "?"
        if len(frames) > 3:
            operation = frames[2].function
        self.log(
            level=constants.LOG_ERROR,
            operation=operation,
            message=error_msg,
            result=str(exception),
        )

        self.state["errors"].append(
            {
                "error_type": type(exception).__name__,
                "error_message": error_msg,
                "exception": exception,
            }
        )

    def errors(self) -> dict:
        return {"errors": self.state["errors"]}

    def logs(self) -> dict:
        return {"logs": self.state["log"]}

    def _flush_state(self):
        self.state = {"log": [], "errors": []}
