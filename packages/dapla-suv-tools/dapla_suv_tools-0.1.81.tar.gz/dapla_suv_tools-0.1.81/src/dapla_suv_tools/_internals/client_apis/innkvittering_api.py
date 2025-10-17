import json

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.decorators import result_to_dict


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext()
def resend_receipts(self, *, context: SuvOperationContext) -> OperationResult:
    """
    Resend receipts for instances in error bucket.
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.
    :return: a json object containing instance data.
    """
    try:
        content: str = client.post(
            path=f"{constants.INNKVITTERING_RESEND_PATH}",
            body_json="{}",
            context=context,
        )
        content_json = json.loads(content)
        context.log(message="Resending receipts for instances in error bucket")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error("Failed to resend receipts", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
