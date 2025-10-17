import json

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.validators import instance_str_validator
from dapla_suv_tools._internals.util.decorators import result_to_dict


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=instance_str_validator)
def get_instance(
    self, *, instance_id: str, context: SuvOperationContext
) -> OperationResult:
    """
    Gets an 'instance' based on it's owner id and guid.
    :param instance_id: The combined instance's owner id and guid separated by a '/' (e.g. '123451213/12345678-1234-1234-1234-123456789012').
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.
    :return: a json object containing instance data.
    """
    try:
        content: str = client.get(
            path=f"{constants.INSTANCE_PATH}/{instance_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message="Fetched 'instance' with id '{instance_id}'")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to fetch for id {instance_id}", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
