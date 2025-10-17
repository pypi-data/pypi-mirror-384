from typing import Optional

from datetime import date
import json

from ssb_altinn3_util.models.skjemadata.skjemadata_request_models import (
    SkjemaRequestModel,
)

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.integration import user_tools
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.validators import (
    skjema_id_validator,
    ra_nummer_validator,
    ra_update_validator,
)
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools.pagination import PaginationInfo
from dapla_suv_tools._internals.util.helpers import bool_to_str


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def get_skjema_by_id(
    self, *, skjema_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Gets a 'skjema' based on it's skjema_id.
    :param skjema_id: The skjema's id
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.
    :return: a json object containing skjema data.
    """
    try:
        content: str = client.get(
            path=f"{constants.SKJEMA_PATH}/{skjema_id}", context=context
        )
        content_json = json.loads(content)

        context.log(message="Fetched 'skjema' with id '{skjema_id}'")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to fetch for id {skjema_id}", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def update_skjema_by_id(
    self,
    *,
    skjema_id: int,
    datamodell: str | None = None,
    beskrivelse: str | None = None,
    navn_nb: str | None = None,
    navn_nn: str | None = None,
    navn_en: str | None = None,
    infoside: str | None = None,
    eier: str | None = None,
    kun_sky: bool | None = None,
    gyldig_fra: date | None = None,
    gyldig_til: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates an existing skjema with the specified skjemea_id. The skjema_id is required, all other parameters are optional. If a parameter is not provided, the existing value will be used.

    Parameters:
    ------------
    skjema_id: int, required
        The id of the skjema to update.
    datamodell: str, optional
        The data model of the skjema.
    beskrivelse: str, optional
        The description of the skjema.
    navn_nb: str, optional
        The name of the skjema in Norwegian Bokmål.
    navn_nn: str, optional
        The name of the skjema in Norwegian Nynorsk.
    navn_en: str, optional
        The name of the skjema in English.
    infoside: str, optional
        URL for the information page of the skjema.
    eier: str, optional
        The owner of the skjema.
    kun_sky: bool, optional
        Whether the skjema is only in the cloud.
    gyldig_fra: date, optional
        The valid from date of the skjema.
    gyldig_til: date, optional
        The valid to date of the skjema.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the updated skjema information, or an error message if the update fails.

    Example:
    ---------
    result = update_skjema_by_id(
        skjema_id=1, gyldig_fra=date(2024, 8, 24), datamodell="test", kun_sky=False, gyldig_til=date(2025, 1, 31)
    )
    """

    user = user_tools.get_current_user(context)
    skjema = get_skjema_by_id(self=self, skjema_id=skjema_id)
    kun_sky_str = bool_to_str(kun_sky) or skjema["kun_sky"]

    body = {
        "id": skjema_id,
        "ra_nummer": skjema["ra_nummer"],
        "versjon": skjema["versjon"],
        "undersokelse_nr": skjema["undersokelse_nr"],
        "datamodell": datamodell or skjema["datamodell"],
        "beskrivelse": beskrivelse or skjema["beskrivelse"],
        "navn_nb": navn_nb or skjema["navn_nb"],
        "navn_nn": navn_nn or skjema["navn_nn"],
        "navn_en": navn_en or skjema["navn_en"],
        "infoside": infoside or skjema["infoside"],
        "eier": eier or skjema["eier"],
        "kun_sky": kun_sky_str,
        "gyldig_fra": gyldig_fra or skjema["gyldig_fra"],
        "gyldig_til": gyldig_til or skjema["gyldig_til"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.SKJEMA_PATH}/{skjema_id}",
            body_json=body_json,
            context=context,
        )

        result: dict = json.loads(content)
        return OperationResult(value=result, log=context.logs())
    except Exception as e:
        context.set_error(f"Update failed for skjema_id {skjema_id}: {e}", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


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
@SuvOperationContext(validator=ra_nummer_validator)
def get_skjema_by_ra_nummer(
    self,
    *,
    ra_nummer: str,
    versjon: Optional[int] = None,
    max_results: int = 0,
    latest_only: bool = False,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Attempts to get all skjema with the supplied RA-number.

    Parameters:
    ------------
    ra_nummer: str, required
        Skjema's RA-number, e.g. 'RA-1234'.
    versjon: int, optional
        Limit the version of the skjema.
    max_results: int, optional
        Maximum number of results int the result set.  A value of 0 will get ALL results.
    latest_only: bool, optional
        Only return the newest entry. Default is False.
    pagination_info: Optional[PaginationInfo]
        An object holding pagination metadata
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        A list of skjema json objects matching the RA-number

    Example:
    --------
    get_skjema_by_ra_nummer(ra_nummer="123456789", versjon=1, max_results=0, latest_only=False, pagination_info=None)

    """

    try:
        filters = (
            json.dumps({"ra_nummer": ra_nummer})
            if versjon is None
            else json.dumps({"ra_nummer": ra_nummer, "versjon": versjon})
        )
        content: str
        if pagination_info is None:
            content = _get_non_paged_result(
                path="/skjemadata/skjema-paged",
                max_results=max_results,
                filters=filters,
                context=context,
            )
        else:
            content = _get_paged_result(
                path="/skjemadata/skjema-paged",
                paging=pagination_info,
                filters=filters,
                context=context,
            )

        result: dict = json.loads(content)

        if latest_only:
            context.log(
                message=f"Fetched latest version of 'skjema' with RA-number '{ra_nummer}'"
            )
            return OperationResult(value=result["results"][0], log=context.logs())

        context.log(message="Fetched all 'skjema' with RA-number '{ra_nummer}'")
        return OperationResult(value=result["results"], log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to fetch for ra_nummer '{ra_nummer}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext()
def get_all_skjema(
    self,
    *,
    max_results: int = 0,
    pagination_info: Optional[PaginationInfo] = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Attempts to get all skjema's.

    Parameters:
    ------------
    max_results: int
        Maximum number of results int the result set.  A value of 0 will get ALL results.
    latest_only: bool
        Only return the newest entry
    pagination_info: Optional[PaginationInfo]
        An object holding pagination metadata
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        A list of all skjema json objects

    Example:
    --------
    get_all_skjema(max_results=0, latest_only=False, pagination_info=None)

    """

    try:
        filters = "{}"
        content: str
        if pagination_info is None:
            content = _get_non_paged_result(
                path="/skjemadata/skjema-paged",
                max_results=max_results,
                filters=filters,
                context=context,
            )
        else:
            content = _get_paged_result(
                path="/skjemadata/skjema-paged",
                paging=pagination_info,
                filters=filters,
                context=context,
            )

        result: dict = json.loads(content)

        context.log(message="Fetched all 'skjema'")
        return OperationResult(value=result["results"], log=context.logs())

    except Exception as e:
        context.set_error("Failed to fetch skjema's.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_update_validator)
def update_skjema_by_ra_number(
    self,
    *,
    ra_nummer: str,
    versjon: int,
    undersokelse_nr: str,
    datamodell: str | None = None,
    beskrivelse: str | None = None,
    navn_nb: str | None = None,
    navn_nn: str | None = None,
    navn_en: str | None = None,
    infoside: str | None = None,
    eier: str | None = None,
    kun_sky: bool = False,
    gyldig_fra: date | None = None,
    gyldig_til: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates a skjema based on the supplied RA-number, versjon and undersokelse_nr. The RA-number, versjon and undersokelse_nr are required, all other parameters are optional. If a parameter is not provided, the existing value will be used.

    Parameters:
    ------------
    ra_nummer: str, required
        Skjema's RA-number, e.g. 'RA-1234'.
    versjon: int, required
        The version of the skjema.
    undersokelse_nr: str, required
        The investigation number of the skjema.
    datamodell: str, optional
        The data model of the skjema.
    beskrivelse: str, optional
        The description of the skjema.
    navn_nb: str, optional
        The name of the skjema in Norwegian Bokmål.
    navn_nn: str, optional
        The name of the skjema in Norwegian Nynorsk.
    navn_en: str, optional
        The name of the skjema in English.
    infoside: str, optional
        URL for the information page of the skjema.
    eier: str, optional
        The owner of the skjema.
    kun_sky: bool, optional
        Whether the skjema is only in the cloud.
    gyldig_fra: date, optional
        The valid from date of the skjema.
    gyldig_til: date, required
        The valid to date of the skjema.
    context: SuvOperationContext
        Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    Returns:
    --------
    dict:
        A list of skjema json objects matching the RA-number

    Example:
    --------
    update_skjema_by_ra_number(
        ra_nummer="RA-1234",
        versjon=1,
        undersokelse_nr="1234",
        gyldig_fra="2024-01-01",
        datamodell="test",
        beskrivelse="test",
        navn_nb="test",
        navn_nn="test",
        navn_en="test",
        infoside="test",
        eier="test",
        kun_sky=False,
        gyldig_til="2023-01-01"
    )

    """

    result = {}

    try:
        filters = json.dumps(
            {
                "ra_nummer": ra_nummer,
                "versjon": versjon,
                "undersokelse_nr": undersokelse_nr,
            }
        )
        content: str = _get_non_paged_result(
            path="/skjemadata/skjema-paged",
            max_results=1,
            filters=filters,
            context=context,
        )

        fetch_skjema: dict = json.loads(content)

        for skjema in fetch_skjema["results"]:
            skjema_id = skjema["id"]
            result = update_skjema_by_id(
                self=self,
                skjema_id=skjema_id,
                datamodell=datamodell or skjema["datamodell"],
                beskrivelse=beskrivelse or skjema["beskrivelse"],
                navn_nb=navn_nb or skjema["navn_nb"],
                navn_nn=navn_nn or skjema["navn_nn"],
                navn_en=navn_en or skjema["navn_en"],
                infoside=infoside or skjema["infoside"],
                eier=eier or skjema["eier"],
                kun_sky=kun_sky or skjema["kun_sky"],
                gyldig_fra=gyldig_fra or skjema["gyldig_fra"],
                gyldig_til=gyldig_til or skjema["gyldig_til"],
            )

        context.log(
            message=f"Updated values for 'skjema' with RA-number '{ra_nummer}', version '{versjon}' and investigation number '{undersokelse_nr}'"
        )
        return OperationResult(value=result, log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to update values for ra_nummer '{ra_nummer}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def create_skjema(
    self,
    *,
    ra_nummer: str,
    versjon: int,
    undersokelse_nr: str,
    gyldig_fra: date,
    datamodell: str | None = None,
    beskrivelse: str | None = None,
    navn_nb: str | None = None,
    navn_nn: str | None = None,
    navn_en: str | None = None,
    infoside: str | None = None,
    eier: str | None = None,
    kun_sky: bool = False,
    gyldig_til: date | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Creates a new version of metadata for the given skjema, based upon the supplied metadata.
    :param self:
    :param ra_nummer:
    :param versjon:
    :param undersokelse_nr:
    :param gyldig_fra:
    :param datamodell:
    :param beskrivelse:
    :param navn_nb:
    :param navn_nn:
    :param navn_en:
    :param infoside:
    :param eier:
    :param kun_sky:
    :param gyldig_til:
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.
    :return:
    """

    user: str = user_tools.get_current_user(context)

    model = SkjemaRequestModel(
        ra_nummer=ra_nummer,
        versjon=versjon,
        undersokelse_nr=undersokelse_nr,
        gyldig_fra=gyldig_fra,
        gyldig_til=gyldig_til,
        endret_av=user,
        datamodell=datamodell,
        beskrivelse=beskrivelse,
        navn_nb=navn_nb,
        navn_nn=navn_nn,
        navn_en=navn_en,
        infoside=infoside,
        eier=eier,
        kun_sky="J" if kun_sky else "N",
    )

    try:
        body = model.model_dump_json()
        content: str = client.post(
            path=constants.SKJEMA_PATH, body_json=body, context=context
        )
        new_id = json.loads(content)["id"]
        # context.log(constants.LOG_INFO, "create_skjema", f"Created 'skjema' with id '{new_id}'")
        context.log(message="Created 'skjema' with id '{new_id}'")
        return OperationResult(value={"id": new_id}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to create for ra_number '{ra_nummer}' - version '{versjon}'", e
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def delete_skjema(
    self, *, skjema_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Attempts to delete the skjema with the supplied id.

    :param skjema_id:
    :param context: Operation context.  This is injected by the underlying pipeline.  Adding a custom context will result in an error.

    :return: A json object containing the operation result.
    """
    try:
        content: str = client.delete(
            path=f"{constants.SKJEMA_PATH}/{skjema_id}", context=context
        )
        context.log(message="Deleted 'skjema' with id '{skjema_id}'")
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to delete skjema with id '{skjema_id}'.", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
