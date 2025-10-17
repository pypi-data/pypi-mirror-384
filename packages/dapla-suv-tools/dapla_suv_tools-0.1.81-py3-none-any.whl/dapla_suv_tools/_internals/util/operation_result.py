from dapla_suv_tools._internals.util import constants,dateUtils


class OperationResult:
    """
    This class is used to return the result of an operation.  It is used to encapsulate the result of an operation
    and log the operation in the context of the operation.
    """

    result_json: dict
    result: str
    operation_log: dict

    def __init__(self, value: dict, success: bool = True, log: dict | None = None):
        if success and isinstance(value, str):
            value = {"result": value}
        self.result = constants.OPERATION_OK if success else constants.OPERATION_ERROR
        self.result_json = value
        self.operation_log = {} if log is None else log
        self.datetime_fields = dateUtils.find_and_convert_datetime_fields(value)

    def process(self, caller) -> dict:
        if hasattr(caller, "operations_log"):
            caller.operations_log.append(self.operation_log)
        if self.result == constants.OPERATION_OK:
            return self.result_json

        if self.result == constants.OPERATION_ERROR:
            if hasattr(caller, "suppress_exceptions") and caller.suppress_exceptions:
                return self.result_json
            errors = self.result_json["errors"]
            raise errors[len(errors) - 1]["exception"]

        return {"result": "Undefined result.  This shouldn't happen."}
