import json
from typing import Optional

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util.validators import (
    ra_nummer_validator,
    delreg_id_validator,
)
from dapla_suv_tools.pagination import PaginationInfo


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)

MAX_PAGE_SIZE = 500
FETCH_EVERYTHING = 1000000


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def get_prefill_isee(
    self,
    *,
    delreg_nr: int,
    ra_nummer: str,
    ident_nr: Optional[str] = None,
    enhets_type: Optional[str] = None,
    felt_ids: Optional[list[str]] = None,
    max_results: int = 0,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Get prefill from isee.

    Parameters:
    ------------
    delreg_nr: int, required
        The delreg number of the selection.
    ra_nummer: str, required
        Skjema's RA-number, e.g. 'RA-1234'.
    ident_nr: str, optional
        The ident number of the person.
    enhets_type: str, optional
        The type of unit.
    felts_ids: list[str], optional
        List of field ids to include in the response.

    Returns:
    --------
    dict:
        A dict object matching the prefill isee

    Example:
    --------
    get_prefill_isee(delreg_nr=123456789, ra_nummer="RA-1234", ident_nr="12345678901", enhets_type="TYPE", felts_ids=["field1", "field2"])

    """

    model = {
        "delreg_nr": delreg_nr,
        "ra_nummer": ra_nummer,
    }

    if ident_nr is not None:
        model["ident_nr"] = ident_nr
    if enhets_type is not None:
        model["enhets_type"] = enhets_type
    if felt_ids is not None:
        model["felt_ids"] = felt_ids

    try:
        content: str
        if pagination_info is not None:
            content: str = _get_paged_result(
                path=f"{constants.SFU_PATH}/prefill-isee",
                body_json=json.dumps(model),
                paging=pagination_info,
                context=context,
            )
        else:
            content = _get_non_paged_result(
                path=f"{constants.SFU_PATH}/prefill-isee",
                body_json=json.dumps(model),
                max_results=max_results,
                context=context,
            )

        result: dict = json.loads(content)
        context.log(message=f"Fetched prefill isee for delreg_nr'{delreg_nr}'")

        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch prefill isee for delreg_nr {delreg_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=delreg_id_validator)
def get_vareliste(
    self,
    *,
    delreg_nr: int,
    ra_nummer: str,
    entity_type: Optional[str] = None,
    katalog_id: Optional[int] = None,
    aktiv: Optional[str] = None,
    felt_ids: Optional[list[str]] = None,
    max_results: int = 0,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Get vareliste.

    Parameters:
    ------------
    delreg_nr: int, required
        The delreg number of the selection.
    ra_nummer: str, required
        Skjema's RA-number, e.g. 'RA-1234'.
    entity_type: str, optional
        The type of entity.
    katalog_id: int, optional
        The catalog ID.
    aktiv: str, optional
        Aktiv status.
    felt_ids: list[str], optional
        List of field ids to include in the response.
    max_results: int, optional
        Specifies the maximum number of results in the returned result.  If 0 or omitted, all results matching the query
        will be returned.  Will be ignored if used together with paginiation_info
    pagination_info: PaginationInfo, optional
        Sets the parameters used for paginating the query results.  Will take precedence over max_results if both are set.
        If omitted, will return the full set, or up to max_results, of the query.  NOTE:  This might take some time for
        large result sets so be patient if retrieving thousands of records!
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        A dict object matching the vareliste

    Example:
    --------
    get_vareliste(delreg_nr=123456789, ra_nummer="RA-1234", entity_type="TYPE", katalog_id=1, aktiv="J", felt_ids=["field1", "field2"])

    """
    model = {
        "delreg_nr": delreg_nr,
        "ra_nummer": ra_nummer,
        "entity_type": entity_type,
        "katalog_id": katalog_id,
        "aktiv": aktiv,
        "felt_ids": felt_ids,
    }

    try:
        content: str
        if pagination_info is None:
            content = _get_non_paged_result(
                path=f"{constants.SFU_PATH}/vareliste/{delreg_nr}",
                body_json=json.dumps(model),
                max_results=max_results,
                context=context,
            )
        else:
            content = _get_paged_result(
                path=f"{constants.SFU_PATH}/vareliste/{delreg_nr}",
                body_json=json.dumps(model),
                paging=pagination_info,
                context=context,
            )

        result: dict = json.loads(content)
        context.log(message=f"Fetched vareliste for delreg_nr'{delreg_nr}'")

        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch vareliste for delreg_nr {delreg_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def get_utvalg_from_sfu(
    self,
    *,
    delreg_nr: int,
    ra_nummer: str,
    pulje: Optional[int] = 0,
    max_results: int = 0,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Get selection from SFU.

    Parameters:
    ------------
    delreg_nr: int, required
        The delreg number of the selection.
    ra_nummer: str, required
        Skjema's RA-number, e.g. 'RA-1234'.
    pulje: int, optional
        Limit the selection by pulje.
    max_results: int, optional
        Specifies the maximum number of results in the returned result.  If 0 or omitted, all results matching the query
        will be returned.  Will be ignored if used together with paginiation_info
    pagination_info: PaginationInfo, optional
        Sets the parameters used for paginating the query results.  Will take precedence over max_results if both are set.
        If omitted, will return the full set, or up to max_results, of the query.  NOTE:  This might take some time for
        large result sets so be patient if retrieving thousands of records!
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        A list of json objects matching the selection

    Example:
    --------
    get_utvalg_from_sfu(delreg_nr="123456789", ra_nummer="123456789", pulje="123456789")

    """

    model = {
        "delreg_nr": delreg_nr,
        "ra_nummer": ra_nummer,
        "pulje_nr": pulje,
    }

    try:
        content: str
        if pagination_info is None:
            content = _get_non_paged_result(
                path=f"{constants.SFU_PATH}/utvalg",
                body_json=json.dumps(model),
                max_results=max_results,
                context=context,
            )
        else:
            content = _get_paged_result(
                path=f"{constants.SFU_PATH}/utvalg",
                body_json=json.dumps(model),
                paging=pagination_info,
                context=context,
            )

        result: dict = json.loads(content)
        context.log(message=f"Fetched selection for delreg_nr'{delreg_nr}'")

        return OperationResult(value=result["items"], log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch for delreg_nr {delreg_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=delreg_id_validator)
def get_enhet_from_sfu(
    self,
    *,
    delreg_nr: int,
    orgnr: str,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Get unit from SFU.

    Parameters:
    ------------
    delreg_nr: int, required
        The delreg number of the selection.
    orgnr: str, required
        The organization number of the unit.
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        An object matching the organization number

    Example:
    --------
    get_enhet_from_sfu(delreg_nr="123456789", orgnr="123456789")

    """

    data = {
        "delreg_nr": delreg_nr,
        "orgnr": orgnr,
    }

    try:
        content: str = client.post(
            path=f"{constants.SFU_PATH}/enhet",
            body_json=json.dumps(data),
            context=context,
        )
        result = json.loads(content)
        context.log(message=f"Fetched org for delreg_nr'{delreg_nr}'")

        return OperationResult(value=result["items"][0], log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to fetch org for delreg_nr {delreg_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


# Helper functions
def _get_non_paged_result(
    path: str, max_results: int, body_json: str, context: SuvOperationContext
) -> str:
    remaining = FETCH_EVERYTHING if max_results == 0 else max_results

    items = []
    page = 1

    while True:
        fetch_size = MAX_PAGE_SIZE if remaining >= MAX_PAGE_SIZE else remaining
        print(f"Fetching {fetch_size} items from page {page}...")
        response = client.post(
            path=f"{path}?page={page}&size={fetch_size}&asc=false",
            body_json=body_json,
            context=context,
        )

        response_json = json.loads(response)
        remaining -= int(response_json["count"])
        print(f"Received {response_json['count']} items.")
        more_results = bool(response_json["hasMore"])
        items.extend(response_json["items"])
        if not more_results or remaining <= 0:
            break

        page += 1

    return json.dumps({"items": items})


def _get_paged_result(
    path: str, paging: PaginationInfo, body_json: str, context: SuvOperationContext
) -> str:
    return client.post(
        path=f"{path}?page={paging.page}&size={paging.size}&asc=false",
        body_json=body_json,
        context=context,
    )
