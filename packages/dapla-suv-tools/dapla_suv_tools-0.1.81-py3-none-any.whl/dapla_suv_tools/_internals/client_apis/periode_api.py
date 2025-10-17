from datetime import date
import json
from typing import Optional
from dapla_suv_tools.pagination import PaginationInfo


from ssb_altinn3_util.models.skjemadata.skjemadata_request_models import (
    PeriodeRequestModel,
)

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.integration import user_tools
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util.validators import (
    periode_id_validator,
    skjema_id_validator,
)

client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


def bool_to_str(value: bool | None, field_name: str = "") -> str | None:
    """Convert a boolean value to a string representation."""
    if field_name == "har_skjemadata":
        return "Y" if value is True else "N"
    return "1" if value is True else "N" if value is False else None


def convert_to_bool(value: str) -> bool:
    """Convert '1' or 'Y' to True, 'N' to False, otherwise return the original value."""
    return True if value in ['1', 'Y'] else False if value == 'N' else value


def _get_non_paged_result(
    path: str, max_results: int, filters: str, context: SuvOperationContext
) -> str:
    if max_results > 0:
        return client.post(
            path=f"{path}?size={max_results}&order_by=versjon&asc=false",
            body_json=filters,
            context=context,
        )

    items = []
    total = 1
    page = 1

    while len(items) < total:
        response = client.post(
            path=f"{path}?page={page}&size=100&order_by=versjon&asc=false",
            body_json=filters,
            context=context,
        )

        response_json = json.loads(response)
        total = int(response_json["total"])
        items.extend(response_json["results"])
        page += 1

    return json.dumps({"results": items})


def _get_paged_result(
    path: str, paging: PaginationInfo, filters: str, context: SuvOperationContext
) -> str:
    return client.post(
        path=f"{path}?page={paging.page}&size={paging.size}&order_by=versjon&asc=false",
        body_json=filters,
        context=context,
    )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def get_periode_by_id(
    self, *, periode_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Retrieves a period by its ID.

    Parameters:
    ------------
    periode_id: int
        The ID of the period to retrieve.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

    Returns:
    --------
    OperationResult:
        An object containing the period information if found, or an error message if the retrieval fails.

    Example:
    ---------
    result = get_periode_by_id(periode_id=123)

    """
    try:
        content: str = client.get(
            path=f"{constants.PERIODE_PATH}/{periode_id}", context=context
        )
        content_json = json.loads(content)

        # Apply conversion to the relevant fields
        content_json['vis_oppgavebyrde'] = convert_to_bool(content_json.get('vis_oppgavebyrde', ''))
        content_json['vis_brukeropplevelse'] = convert_to_bool(content_json.get('vis_brukeropplevelse', ''))
        content_json['har_skjemadata'] = convert_to_bool(content_json.get('har_skjemadata', ''))

        context.log(message=f"Fetched periode with periode_id '{periode_id}'")

        return OperationResult(value=content_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for id {periode_id}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def get_perioder_by_skjema_id(
    self,
    *,
    skjema_id: int,
    periode_type: Optional[str] = None,  # Optional type parameter
    periode_nr: Optional[int] = None,  # Optional nummer parameter
    periode_aar: Optional[int] = None,
    delreg_nr: Optional[int] = None,
    enhet_type: Optional[int] = None,
    max_results: int = 0,
    latest_only: bool = False,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
     Retrieves periods associated with a specific schema ID.

    Parameters:
    ------------
    skjema_id: int
        The skjema_id of the schema for which to retrieve periods.
    periode_type: Optional[str]
        The type of the period to filter by. If None, periods of any type will be retrieved.
    periode_nr: Optional[int]
        The number of the period to filter by. If None, periods of any number will be retrieved.
    periode_aar: Optional[int]
        The year of the period to filter by. If None, periods of any year will be retrieved.
    delreg_nr: Optional[int]
        The delreg_nr of the period to filter by. If None, periods of any delreg_nr will be retrieved.
    enhet_type: Optional[int]
        The enhet_type of the period to filter by. If None, periods of any enhet_type will be retrieved.
    max_results: int
        Maximum number of results in the result set. A value of 0 will get ALL results. Defaults to 0
    latest_only: bool
        A boolean flag to trigger a special condition. A True value will retrieve the latest periode added. Defaults to False.
    pagination_info: Optional[int]
        An object holding pagination metadata. Defaults to None.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing a list of periods associated with the schema ID, or an error message if the retrieval fails.

    Example:
    ---------
    result = get_perioder_by_skjema_id(
        skjema_id=456, periode_type="KVRT", periode_aar=2023
    )
    """

    try:
        filters = {
            "skjema_id": skjema_id,
            "periode_type": periode_type,
            "periode_nr": periode_nr,
            "periode_aar": periode_aar,
            "delreg_nr": delreg_nr,
            "enhet_type": enhet_type,
        }
        filters_json = json.dumps(filters)
        content: str
        if pagination_info is None:
            content = _get_non_paged_result(
                path="/periode/periode-paged",
                max_results=max_results,
                filters=filters_json,
                context=context,
            )
        else:
            content = _get_paged_result(
                path="/periode/periode-paged",
                paging=pagination_info,
                filters=filters_json,
                context=context,
            )

        result: dict = json.loads(content)

        for item in result["results"]:
            item["vis_oppgavebyrde"] = convert_to_bool(item.get("vis_oppgavebyrde", ''))
            item["vis_brukeropplevelse"] = convert_to_bool(item.get("vis_brukeropplevelse", ''))
            item["har_skjemadata"] = convert_to_bool(item.get("har_skjemadata", ''))

        if latest_only:
            context.log(
                message=f"Fetched latest version of 'periode' with skjemda id '{skjema_id}'"
            )
            return OperationResult(value=result["results"][0], log=context.logs())

        context.log(message="Fetched all 'perioder' with skjema id '{skjema_id}'")
        return OperationResult(value=result["results"], log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to fetch periode for skjema id '{skjema_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def update_periode_by_id(
    self,
    *,
    periode_id: int,
    periode_dato: date | None = None,
    delreg_nr: int | None = None,
    enhet_type: str | None = None,
    vis_oppgavebyrde: bool | None = None,
    vis_brukeropplevelse: bool | None = None,
    har_skjemadata: bool | None = None,
    journalnummer: str | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates an existing period with the specified periode_id.

    Parameters:
    ------------
    periode_id: int
        The ID of the period to update.
    periode_dato: Optional[date]
        Date for the period. If None, the existing date will be used.
    delreg_nr: Optional[int]
        delreg_nr. If None, the existing number will be used.
    enhet_type: Optional[str]
        enhet_type. If None, the existing type will be used.
    vis_oppgavebyrde: Optional[bool]
        A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
    vis_brukeropplevelse: Optional[bool]
        A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
    har_skjemadata: Optional[bool]
        A boolean flag to indicate the presence of schema data. Defaults to None.
    journalnummer: Optional[str]
        Journal number. If None, the existing number will be used.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated period information, or an error message if the update fails.

    Example:
    ---------
    result = update_periode_by_id(
        periode_id=456, vis_oppgavebyrde=True, date(2024,12,15)
    )
    """

    user = user_tools.get_current_user(context)

    periode = get_periode_by_id(self=self, periode_id=periode_id)

    # Convert boolean to string using the helper function.
    vis_oppgavebyrde_str = bool_to_str(vis_oppgavebyrde) if vis_oppgavebyrde is not None else bool_to_str(periode["vis_oppgavebyrde"])
    vis_brukeropplevelse_str = bool_to_str(vis_brukeropplevelse) if vis_brukeropplevelse is not None else bool_to_str(periode["vis_brukeropplevelse"])
    har_skjemadata_str = bool_to_str(har_skjemadata, "har_skjemadata") if har_skjemadata is not None else bool_to_str(periode["har_skjemadata"], "har_skjemadata")

    body = {
        "id": periode_id,
        "skjema_id": periode["skjema_id"],
        "periode_type": periode["periode_type"],
        "periode_nr": periode["periode_nr"],
        "periode_aar": periode["periode_aar"],
        "periode_dato": periode_dato.isoformat()
        if periode_dato is not None
        else periode["periode_dato"],
        "delreg_nr": delreg_nr if delreg_nr is not None else periode["delreg_nr"],
        "enhet_type": enhet_type if enhet_type is not None else periode["enhet_type"],
        "vis_oppgavebyrde": vis_oppgavebyrde_str,
        "vis_brukeropplevelse": vis_brukeropplevelse_str,
        "har_skjemadata": har_skjemadata_str,
        "journalnummer": journalnummer
        if journalnummer is not None
        else periode["journalnummer"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.PERIODE_PATH}/{periode_id}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)

        for key in ['vis_brukeropplevelse', 'vis_oppgavebyrde', 'har_skjemadata']:
            if key in result:
                result[key] = convert_to_bool(result[key])
        
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to update periode for periode_id {periode_id}",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def update_periode_by_skjema_id(
    self,
    *,
    skjema_id: int,
    periode_type: str,
    periode_aar: int,
    periode_nr: int,
    periode_dato: date | None = None,
    delreg_nr: int | None = None,
    enhet_type: str | None = None,
    vis_oppgavebyrde: bool | None = None,
    vis_brukeropplevelse: bool | None = None,
    har_skjemadata: bool | None = None,
    journalnummer: str | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """

    Updates an existing period with the specified skjema_id.

    Parameters:
    ------------
    skjema_id: int
        The skjema_id of the period to update.
    periode_type: str
        Periode type of the period to update.
    periode_aar: int
        Year of the period to update.
    periode_nr: int
        Periode number of the period to update.
    periode_dato: Optional[date]
        Date for the period. If None, the existing date will be used.
    delreg_nr: Optional[int]
        delreg_nr. If None, the existing number will be used.
    enhet_type: Optional[str]
        Unit type. If None, the existing type will be used.
    vis_oppgavebyrde: Optional[bool]
        A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
    vis_brukeropplevelse: Optional[bool]
        A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
    har_skjemadata: Optional[bool]
        A boolean flag to indicate the presence of schema data. Defaults to None.
    journalnummer: Optional[str]
        Journal number. If None, the existing number will be used.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated period information, or an error message if the update fails.

    Example:
    ---------
    result = update_periode_by_skjema_id(
        skjema_id=456, periode_type="KVRT", periode_aar=2023, date(2024,12,15), periode_nr=1
    )
    """

    user = user_tools.get_current_user(context)

    periode_list = get_perioder_by_skjema_id(
        self=self,
        skjema_id=skjema_id,
        periode_type=periode_type,
        periode_aar=periode_aar,
        periode_nr=periode_nr,
    )

    periode = periode_list[0]
 
    # Convert boolean to string using the helper function.
    vis_oppgavebyrde_str = bool_to_str(vis_oppgavebyrde) if vis_oppgavebyrde is not None else bool_to_str(periode["vis_oppgavebyrde"])
    vis_brukeropplevelse_str = bool_to_str(vis_brukeropplevelse) if vis_brukeropplevelse is not None else bool_to_str(periode["vis_brukeropplevelse"])
    har_skjemadata_str = bool_to_str(har_skjemadata, "har_skjemadata") if har_skjemadata is not None else bool_to_str(periode["har_skjemadata"], "har_skjemadata")

    body = {
        "id": periode["id"],
        "skjema_id": skjema_id,
        "periode_type": periode["periode_type"],
        "periode_nr": periode["periode_nr"],
        "periode_aar": periode["periode_aar"],
        "periode_dato": periode_dato.isoformat()
        if periode_dato is not None
        else periode["periode_dato"],
        "delreg_nr": delreg_nr if delreg_nr is not None else periode["delreg_nr"],
        "enhet_type": enhet_type if enhet_type is not None else periode["enhet_type"],
        "vis_oppgavebyrde": vis_oppgavebyrde_str,
        "vis_brukeropplevelse": vis_brukeropplevelse_str,
        "har_skjemadata": har_skjemadata_str,
        "journalnummer": journalnummer
        if journalnummer is not None
        else periode["journalnummer"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.PERIODE_PATH}/{periode['id']}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)
        
        for key in ['vis_brukeropplevelse', 'vis_oppgavebyrde', 'har_skjemadata']:
            if key in result:
                result[key] = convert_to_bool(result[key])
        
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to update periode for skjema_id {skjema_id} - periode {periode_nr} {periode_type} {periode_nr} ",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def create_periode(
    self,
    *,
    skjema_id: int,
    periode_type: str | None = None,
    periode_nr: int | None = None,
    periode_aar: int | None = None,
    periode_dato: date | None = None,
    delreg_nr: int | None = None,
    enhet_type: str | None = None,
    vis_oppgavebyrde: bool | None = False,
    vis_brukeropplevelse: bool | None = False,
    har_skjemadata: bool | None = False,
    journalnummer: str | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Creates a new period with the specified details.

    Parameters:
    ------------
    skjema_id: int
        The skjema_id associated with the new period.
    periode_type: Optional[str]
        Periode type of the new periode.
    periode_aar: Optional[int]
        Year of the new periode.
    periode_nr: Optional[int]
        Periode number of the new periode.
    periode_dato: Optional[date]
        Date for the period.
    delreg_nr: Optional[int]
        delreg_nr.
    enhet_type: Optional[str]
        enhet_type.
    vis_oppgavebyrde: Optional[bool]
        A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
    vis_brukeropplevelse: Optional[bool]
        A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
    har_skjemadata: Optional[bool]
        A boolean flag to indicate the presence of schema data. Defaults to None.
    journalnummer: Optional[str]
        journalnummer. Defaults to None.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the ID of the created period, or an error message if the creation fails.

    Example:
    ---------
    result = create_periode(
        skjema_id=456, periode_type="KVRT", periode_aar=2023, date(2024,12,15),periode_nr=1
    )
    """

    vis_oppgavebyrde_str = bool_to_str(vis_oppgavebyrde)
    vis_brukeropplevelse_str = bool_to_str(vis_brukeropplevelse)
    har_skjemadata_str = bool_to_str(har_skjemadata, "har_skjemadata") 

    user = user_tools.get_current_user(context)

    model = PeriodeRequestModel(
        skjema_id=skjema_id,
        endret_av=user,
        periode_type=periode_type,
        periode_nr=periode_nr,
        periode_aar=periode_aar,
        periode_dato=periode_dato.isoformat() if periode_dato else None,
        delreg_nr=delreg_nr,
        enhet_type=enhet_type,
        vis_oppgavebyrde=vis_oppgavebyrde_str,
        vis_brukeropplevelse=vis_brukeropplevelse_str,
        har_skjemadata=har_skjemadata_str,
        journalnummer=journalnummer,
    )
    
    try:
        body = model.model_dump_json()
        content: str = client.post(
            path=constants.PERIODE_PATH, body_json=body, context=context
        )
        new_id = json.loads(content)["id"]
        context.log(message="Created 'periode' with id '{new_id}'")
        
        return OperationResult(value={"id": new_id}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to create for skjema_id '{skjema_id}' - periode {periode_nr} {periode_type} {periode_nr}",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def delete_periode(
    self, *, periode_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Deletes the period with the specified periode_id.

    Parameters:
    ------------
    periode_id: int
        The ID of the period to delete.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the result of the deletion operation, or an error message if the deletion fails.

    Example:
    ---------
    result = delete_periode(
        Periode_id=123
    )
    """
    try:
        content: str = client.delete(
            path=f"{constants.PERIODE_PATH}/{periode_id}", context=context
        )
        context.log(message="Deleted 'periode' with id '{periode_id}'")
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to delete Periode with id '{periode_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=periode_id_validator)
def create_new_periodes(
    self,
    *,
    periode_id: int,
    num_new_periodes: int, 
    context: SuvOperationContext,
) -> OperationResult:
    """
    Creates new periodes using a given exisiting period. 

    Parameters:
    ------------
    periode_id: int
        The periode_id associated with the new periods.
    num_new_periodes: int 
        Number of new periodes to be created
   
    Returns:
    --------
    OperationResult:
        An object containing the ID of the created periodes, or an error message if the creation fails.

    Example:
    ---------
    result = create_new_periodes(periode_id=80, num_new_periodes=3)
    """

    try:
        content: str = client.post(
            path=f"{constants.PERIODE_PATH}/{periode_id}/create-new/{num_new_periodes}", body_json="", context=context
        )
        context.log(message="Created {num_new_periods} new periodes using period with id '{periode_id}'")
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to create Periodes using period_id '{periode_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
