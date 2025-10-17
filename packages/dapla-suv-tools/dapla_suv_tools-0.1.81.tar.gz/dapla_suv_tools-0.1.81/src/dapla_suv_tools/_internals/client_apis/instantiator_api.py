import json

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.decorators import result_to_dict


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext()
def resend_instances(
    self, *, filters: str, context: SuvOperationContext
) -> OperationResult:
    """
    Resend 'instances' based on it's batch_ref, ra_number, period or reportee_id. If no filters are provided, all failed instances will be resent.
    :param filters: The filters to apply to the instances. Sample filters: {"batch_ref": "123", "ra_number": "123", "period": "2021-01", "reportee_id": "123"}
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.
    :return: a json object containing instance data.
    """
    try:
        content: str = client.post(
            path=f"{constants.INSTANTIATOR_RESEND_PATH}",
            body_json=json.dumps(filters),
            context=context,
        )
        content_json = json.loads(content)
        context.log(message="Resending instances based on filters")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error("Failed resend instances", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
