import json
from datetime import date, datetime
from dapla_suv_tools._internals.util import dateUtils

from ssb_altinn3_util.models.skjemadata.skjemadata_request_models import (
    PuljeRequestModel,
)

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.integration import user_tools
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util.validators import (
    pulje_id_validator,
    periode_id_validator
)

client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=pulje_id_validator)
def get_pulje_by_id(
    self, *, pulje_id: int, context: SuvOperationContext
) -> OperationResult:
    
    """
    Retrieves a pulje by its ID.

    Parameters:
    ------------
    pulje_id: int
        The ID of the pulje to retrieve.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

    Returns:
    --------
    OperationResult:
        An object containing the pulje information if found, or an error message if the retrieval fails.
    
    Example:
    ---------
    result = get_pulje_by_id(pulje_id=123)

    """
    try:
        content: str = client.get(
            path=f"{constants.PULJE_PATH}/{pulje_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message=f"Fetched pulje with pulje_id '{pulje_id}'")

        return OperationResult(value=content_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for id {pulje_id}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def get_pulje_by_periode_id(
    self, *, periode_id: int, context: SuvOperationContext
) -> OperationResult:
    
    """
    Retrieves a pulje by its periode_id.

    Parameters:
    ------------
    periode_id: int
        The periode_id of the pulje to retrieve.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

    Returns:
    --------
    OperationResult:
        A list of objects containing the pulje information for every pulje under the given pulje_id if found, or an error message if the retrieval fails.
    
    Example:
    ---------
    result = get_pulje_by_periode_id(periode_id=123)

    """
    try:
        content: str = client.get(
            path=f"{constants.PULJE_PATH}/periode/{periode_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message=f"Fetched pulje with periode_id '{periode_id}'")

        return OperationResult(value=content_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for id {periode_id}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def create_pulje(
    self,
    *,
    periode_id: int,
    pulje_nr: int | None = None,
    altinn_tilgjengelig: datetime | None = None,
    altinn_svarfrist: date | None = None,
    tvangsmulkt_svarfrist: date | None = None,
    send_si: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:

    """
    Creates a new pulje with the specified details.

    Parameters:
    ------------
    periode_id: int
        The periode_id associated with the new pulje.
    pulje_nr: Optional[int]
        pulje_nr of the new pulje. Has to be unique under the same periode_id if is going to be set. 
    altinn_tilgjengelig: Optional[datetime] # Year, Month, Day, Hour, Minute, Second (24Hour format)
        Date and time for altinn_tilgjengelig.
    altinn_svarfrist: Optional[date]
        Date for altinn_svarfrist.
    tvangsmulkt_svarfrist: Optional[date]
        Date for tvangsmulkt_svarfrist.
    send_si: Optional[date]
        Date for send_si.    
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the ID of the created pulje, or an error message if the creation fails.

    Example:
    ---------
    result = create_pulje(
        pulje_id=456, pulje_nr=1, altinn_tilgjengelig=datetime(2023,12,15,14,30,45), send_si=date(2023,10,12)
    )
    """    

    existing_puljer = get_pulje_by_periode_id(self=self, periode_id=periode_id)

    if pulje_nr is not None:
        if any(pulje['pulje_nr'] == pulje_nr for pulje in existing_puljer if pulje['pulje_nr'] is not None):
            return OperationResult(
                success=False,
                value={"message": f"Pulje_nr {pulje_nr} already exists for periode_id {periode_id}."},
                log=context.logs()
            )
    
    user = user_tools.get_current_user(context)

    # Convert altinn_tilgjengelig to UTC if it’s provided
    utc_altinn_tilgjengelig = dateUtils.convert_to_utc(altinn_tilgjengelig) if altinn_tilgjengelig else None

    model = PuljeRequestModel(
        periode_id=periode_id,
        pulje_nr=pulje_nr,
        altinn_tilgjengelig=utc_altinn_tilgjengelig,
        altinn_svarfrist=altinn_svarfrist,
        tvangsmulkt_svarfrist=tvangsmulkt_svarfrist,
        send_si=send_si,
        endret_av=user
    )

    try:
        body = model.model_dump_json()
        content: str = client.post(
            path=constants.PULJE_PATH, body_json=body, context=context
        )
        new_id = json.loads(content)["id"]
        context.log(message="Created 'pulje' with id '{new_id}'")
        return OperationResult(value={"id": new_id}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to create pulje for periode_id '{periode_id}'",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=pulje_id_validator)
def update_pulje_by_id(
    self,
    *,
    pulje_id: int,
    altinn_tilgjengelig: datetime | None = None,
    altinn_svarfrist: date | None = None,
    tvangsmulkt_svarfrist: date | None = None,
    send_si: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates an existing pulje with the specified pulje_id.

    Parameters:
    ------------
    pulje_id: int
        The ID of the period to update.
    altinn_tilgjengelig: Optional[datetime] # Year, Month, Day, Hour, Minute, Second (24Hour format)
        Date and time for altinn_tilgjengelig.
    altinn_svarfrist: Optional[date]
        Date for altinn_svarfrist.
    tvangsmulkt_svarfrist: Optional[date]
        Date for tvangsmulkt_svarfrist.
    send_si: Optional[date]
        Date for send_si.   
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated pulje information, or an error message if the update fails.

    Example:
    ---------
    result = update_pulje_by_id(
        pulje_id=456, send_si=date(2023,10,12)
    )
    """

    user = user_tools.get_current_user(context)

    pulje = get_pulje_by_id(self=self, pulje_id=pulje_id)

    body = {
        "id": pulje_id,
        "periode_id": pulje["periode_id"],
        "pulje_nr": pulje["pulje_nr"],
        "altinn_tilgjengelig": dateUtils.convert_to_utc(altinn_tilgjengelig).isoformat() if altinn_tilgjengelig else pulje["altinn_tilgjengelig"],
        "altinn_svarfrist": altinn_svarfrist.isoformat() if altinn_svarfrist else pulje["altinn_svarfrist"],
        "tvangsmulkt_svarfrist": tvangsmulkt_svarfrist.isoformat() if tvangsmulkt_svarfrist else pulje["tvangsmulkt_svarfrist"],
        "send_si": send_si.isoformat() if send_si else pulje["send_si"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.PULJE_PATH}/{pulje_id}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to update pulje for pulje_id {pulje_id}",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


def find_pulje_by_pulje_nr(puljer, pulje_nr):
    # Iterate through the list of puljer and find the one with the matching pulje_nr
    for pulje in puljer:
        if pulje['pulje_nr'] == pulje_nr:
            return pulje
    # Return None if no pulje with the specified pulje_nr is found
    return None


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def update_pulje_by_periode_id(
    self,
    *,
    periode_id: int,
    pulje_nr: int,
    altinn_tilgjengelig: datetime | None = None,
    altinn_svarfrist: date | None = None,
    tvangsmulkt_svarfrist: date | None = None,
    send_si: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates an existing pulje with the specified periode_id and pulje.

    Parameters:
    ------------
    periode_id: int
        The ID of the pulje to update.
    pulje_nr: int
        The pulje_nr of the period to update.    
    altinn_tilgjengelig: Optional[datetime] # Year, Month, Day, Hour, Minute, Second (24Hour format)
        Date and time for altinn_tilgjengelig.
    altinn_svarfrist: Optional[date]
        Date for altinn_svarfrist.
    tvangsmulkt_svarfrist: Optional[date]
        Date for tvangsmulkt_svarfrist.
    send_si: Optional[date]
        Date for send_si.   
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated pulje information, or an error message if the update fails.

    Example:
    ---------
    result = update_pulje_by_periode_id(
        periode_id=456, pulje_nr=2, tvangsmulkt_svarfrist=date(2024,11,13)
    )
    """

    # Retrieve all puljer for the given periode_id
    puljer = get_pulje_by_periode_id(self=self, periode_id=periode_id)
    pulje = find_pulje_by_pulje_nr(puljer, pulje_nr)

    if pulje is None:
        return OperationResult(
                success=False,
                value={"message": f"Pulje_nr {pulje_nr} does not exist exists for periode_id {periode_id}."},
                log=context.logs()
            )

    user = user_tools.get_current_user(context)
    body = {
        "id": pulje["id"],
        "periode_id": periode_id,
        "pulje_nr": pulje_nr,
        "altinn_tilgjengelig": dateUtils.convert_to_utc(altinn_tilgjengelig).isoformat() if altinn_tilgjengelig else pulje["altinn_tilgjengelig"],
        "altinn_svarfrist": altinn_svarfrist.isoformat() if altinn_svarfrist else pulje["altinn_svarfrist"],
        "tvangsmulkt_svarfrist": tvangsmulkt_svarfrist.isoformat() if tvangsmulkt_svarfrist else pulje["tvangsmulkt_svarfrist"],
        "send_si": send_si.isoformat() if send_si else pulje["send_si"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)

        content: str = client.put(
            path=f"{constants.PULJE_PATH}/{pulje['id']}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)
        
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to update pulje for periode_id {periode_id}",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=pulje_id_validator)
def delete_pulje(
    self, *, pulje_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Deletes the pulje with the specified pulje_id.

    Parameters:
    ------------
    pulje_id: int
        The pulje_id of the pulje to delete.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the result of the deletion operation, or an error message if the deletion fails.

    Example:
    ---------
    result = delete_pulje(
        pulje_id=123
    )
    """
    try:
        content: str = client.delete(
            path=f"{constants.PULJE_PATH}/{pulje_id}", context=context
        )
        context.log(message="Deleted 'pulje' with id '{pulje_id}'")
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to delete pulje with id '{pulje_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
