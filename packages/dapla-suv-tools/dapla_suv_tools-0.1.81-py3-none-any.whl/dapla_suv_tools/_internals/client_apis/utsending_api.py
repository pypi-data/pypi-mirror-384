import json
from datetime import datetime

from ssb_altinn3_util.models.skjemadata.skjemadata_request_models import (
    UtsendingRequestModel,
)

from dapla_suv_tools._internals.integration import user_tools
from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util import constants, dateUtils
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util.validators import (
    pulje_id_validator,
    utsending_id_validator
)

client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=utsending_id_validator)
def get_utsending_by_id(
    self, *, utsending_id: int, context: SuvOperationContext
) -> OperationResult:
    
    """
    Retrieves an utsending by its ID.

    Parameters:
    ------------
    utsending_id: int
        The ID of the utsending to retrieve.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

    Returns:
    --------
    OperationResult:
        An object containing the utsending information if found, or an error message if the retrieval fails.
    
    Example:
    ---------
    result = get_utsending_by_id(utsending_id=123)

    """
    try:
        content: str = client.get(
            path=f"{constants.UTSENDING_PATH}/{utsending_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message=f"Fetched utsending with utsending_id '{utsending_id}'")

        return OperationResult(value=content_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for id {utsending_id}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=pulje_id_validator)
def get_utsending_by_pulje_id(
    self, *, pulje_id: int, context: SuvOperationContext
) -> OperationResult:
    
    """
    Retrieves a pulje by its pulje_id.

    Parameters:
    ------------
    pulje_id: int
        The pulje_id of the utsending to retrieve.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

    Returns:
    --------
    OperationResult:
        A list of objects containing the utsending information for every utsending under the given pulje_id if found, or an error message if the retrieval fails.
    
    Example:
    ---------
    result = get_utsending_by_pulje_id(pulje_id=123)

    """
    try:
        content: str = client.get(
            path=f"{constants.UTSENDING_PATH}/pulje/{pulje_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message=f"Fetched utsending with pulje_id '{pulje_id}'")

        return OperationResult(value=content_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for id {pulje_id}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=utsending_id_validator)
def update_utsending_by_id(
    self,
    *,
    utsending_id: int,
    utsendingstype_navn: str | None = None,
    trigger: str | None = None,
    test: bool | None = None,
    altinn_uts_tidspunkt: datetime | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates an existing utsending with the specified utsending_id.

    Parameters:
    ------------
    utsending_id: int
        The ID of the utsending to update.
    utsendingstype_navn: Optional(str)
        utsendingstype_navn for utsending to update
    trigger: Optional(str)
        trigger
    test: Optional(bool) 
        test
    altinn_uts_tidspunkt: Optional(datetime)
        altinn_uts_tidspunkt
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated utsending information, or an error message if the update fails.

    Example:
    ---------
    result = update_utsending_by_id(
        utsending_id=456,utsendingstype_navn="instansiering", trigger="Manuell", altinn_uts_tidspunkt=datetime(2023,10,12)
    )
    """
    
    user = user_tools.get_current_user(context)

    utsending = get_utsending_by_id(self=self, utsending_id=utsending_id)
    utsendingstype_id = utsending["utsendingstype_id"]  # Default to current value
    if utsendingstype_navn:
        try:
            content: str = client.get(
                path=f"{constants.UTSENDINGSTYPE_PATH}/navn/{utsendingstype_navn}",
                context=context
            )
            content_json = json.loads(content)
            utsendingstype_id = content_json['id']
        except Exception as e:
            context.set_error(
                f"Failed to retrieve utsendingstype_id for navn {utsendingstype_navn}",
                e,
            )
            return OperationResult(
                success=False, value=context.errors(), log=context.logs()
            )

    body = {
        "id": utsending_id,
        "pulje_id": utsending["pulje_id"],
        "utsendingstype_id": utsendingstype_id,
        "utsendingstype_navn": utsendingstype_navn if utsendingstype_navn else utsending["utsendingstype_navn"],
        "trigger": trigger if trigger else utsending["trigger"],
        "test": test if test is not None else utsending["test"],
        "altinn_uts_tidspunkt": dateUtils.convert_to_utc(altinn_uts_tidspunkt).isoformat() if altinn_uts_tidspunkt else utsending["altinn_uts_tidspunkt"],
        "endret_av": user,
    }
   

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.UTSENDING_PATH}/{utsending_id}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to update utsending for utsending_id {utsending_id}",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
    

@result_to_dict
@SuvOperationContext(validator=pulje_id_validator)
def create_utsending(
    self,
    *,
    pulje_id: int,
    utsendingstype_navn: str | None = None,
    trigger: str | None = "Manuell",
    test: bool | None = False,
    altinn_uts_tidspunkt: datetime | None = None,
    context: SuvOperationContext,
) -> OperationResult:

    """
    Creates a new utsending with the specified details.

    Parameters:
    ------------
    pulje_id: int
        The pulje_id associated with the new utsending.
    utsendingstype_navn: Optional(str)
        utsendingstype_navn for utsending to create
    trigger: Optional(str)
        trigger
    test: Optional(bool) 
        test
    altinn_uts_tidspunkt: Optional(datetime)
        altinn_uts_tidspunkt
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the ID of the created utsending, or an error message if the creation fails.

    Example:
    ---------
    result = create_utsending(
        pulje_id=456, test=True
    )
    """
    try:
        content: str = client.get(
            path=f"{constants.UTSENDINGSTYPE_PATH}/navn/{utsendingstype_navn}", context=context
        )
        content_json = json.loads(content)
        utsendingstype_id = content_json['id']
        context.log(message=f"Fetched utsendingtype with utsendingstype_navn '{utsendingstype_navn}'")
    except Exception as e:
        context.set_error(
            f"Failed to get utsendingtype_id for utsendingstype_navn '{utsendingstype_navn}'",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )

    user = user_tools.get_current_user(context)

    utc_altinn_uts_tidspunkt = dateUtils.convert_to_utc(altinn_uts_tidspunkt) if altinn_uts_tidspunkt else None

    model = UtsendingRequestModel(
        pulje_id=pulje_id,
        utsendingstype_navn=utsendingstype_navn,
        utsendingstype_id=utsendingstype_id,
        trigger=trigger,
        test=test,
        altinn_uts_tidspunkt=utc_altinn_uts_tidspunkt,
        endret_av=user
    )

    try:
        body = model.model_dump_json()
        content: str = client.post(
            path=constants.UTSENDING_PATH, body_json=body, context=context
        )
        new_id = json.loads(content)["id"]
        context.log(message="Created 'utsending' with id '{new_id}'")
        return OperationResult(value={"id": new_id}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to create utsending for pulje_id '{pulje_id}'",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=utsending_id_validator)
def delete_utsending(
    self, *, utsending_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Deletes the utsending with the specified utsending_id.

    Parameters:
    ------------
    utsending_id: int
        The utsending_id of the utsending to delete.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the result of the deletion operation, or an error message if the deletion fails.

    Example:
    ---------
    result = delete_utsending(
        utsending_id=123
    )
    """
    try:
        content: str = client.delete(
            path=f"{constants.UTSENDING_PATH}/{utsending_id}", context=context
        )
        context.log(message="Deleted 'utsending' with id '{utsending_id}'")
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to delete utsending with id '{utsending_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
