import json
from typing import Optional

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.operation_result import OperationResult
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants
from dapla_suv_tools._internals.util.validators import (
    skjema_id_validator,
    ra_nummer_validator,
    prefill_meta_id_validator,
)
from dapla_suv_tools._internals.util.decorators import result_to_dict
from ssb_altinn3_util.models.skjemadata.skjemadata_request_models import (
    SkjemaPrefillMetaRequestModel,
)
from dapla_suv_tools._internals.integration import user_tools


client = SuvApiClient(base_url=constants.END_USER_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def get_prefill_meta_by_skjema_id(
    self, *, skjema_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Gets prefill meta for a 'skjema' based on it's skjema_id.

    Parameters:
    ------------
    skjema_id: int, required
        The skjema_id associated with the new period.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        A list of json objects containing the skjema's prefill meta data

    Example:
    ---------
    result = get_prefill_meta_by_skjema_id(
        skjema_id=123
    )
    """

    try:
        content: str = client.get(
            path=f"{constants.PREFILL_META_PATH}/skjema/{skjema_id}", context=context
        )
        content_json = json.loads(content)
        # context.log(constants.LOG_INFO, "get_skjema_by_id", f"Fetched 'skjema' with id '{skjema_id}'")
        context.log(message="Fetched 'skjema' with id '{skjema_id}'")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(f"Failed to fetch for id {skjema_id}", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext()
def get_prefill_meta_paged(self, *, context: SuvOperationContext) -> OperationResult:
    try:
        content: str = client.post(
            path=f"{constants.PREFILL_META_PATH}-paged", context=context, body_json={}
        )
        content_json = json.loads(content)
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error("Failed to fetch prefill meta", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=prefill_meta_id_validator)
def get_prefill_meta_by_prefill_meta_id(
    self, *, prefill_meta_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Gets prefill meta based on it's prefill_meta_id.

    Parameters:
    ------------
    prefill_meta_id: int, required
        The prefill_meta_id associated with the prefill meta.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        an object containing prefill meta data

    Example:
    ---------
    result = get_prefill_meta_by_prefill_meta_id(
        prefill_meta_id=123
    )
    """

    try:
        content: str = client.get(
            path=f"{constants.PREFILL_META_PATH}/{prefill_meta_id}", context=context
        )
        content_json = json.loads(content)
        context.log(message="Fetched 'prefill meta for prefill_meta_id '{skjema_id}'")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(
            f"Failed to fetch prefill meta for prefill_meta_id {prefill_meta_id}", e
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def get_prefill_meta_by_skjema_def(
    self,
    *,
    ra_nummer: str,
    versjon: int,
    undersokelse_nr: str,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Gets prefill meta for a 'skjema' based on it's skjema_def.

    Parameters:
    ------------
    ra_nummer : str
        The RA number associated with the skjema.
    versjon : int
        The version number of the skjema.
    undersokelse_nr : str
        The survey number linked to the skjema.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
       A json objects containing the skjema's prefill meta data

    Example:
    ---------
    result = get_prefill_meta_by_skjema_def(
        ra_nummer="RA-0666A3",
        versjon= 1,
        undersokelse_nr=1060
    )
    """

    try:
        content: str = client.get(
            path=f"{constants.PREFILL_META_PATH}/skjema/{ra_nummer}/{versjon}/{undersokelse_nr}",
            context=context,
        )
        content_json = json.loads(content)

        context.log(
            message="Fetched prefill for skjema_def ra_nummer: {ra_nummer}, versjon: {versjon}, undersokelse_nr: {undersokelse_nr}'"
        )
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(
            f"Failed to fetch for skjema_def ra_nummer: {ra_nummer}, versjon: {versjon}, undersokelse_nr: {undersokelse_nr},",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def save_prefill_meta(
    self,
    *,
    skjema_id: int,
    navn: str,
    obligatorisk: bool,
    sti: Optional[str] | None = None,
    type: Optional[str] | None = "ORDINAR",
    min: Optional[int] | None = None,
    maks: Optional[int] | None = None,
    dublett_sjekk: Optional[bool] | None = False,
    stat_navn: Optional[str] | None = None,
    kommentar: Optional[str] | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Creates prefill meta for given skjema_id

    Parameters:
    ------------
    skjema_id : int, required
        The ID of the skjema associated with the prefill meta.
    navn : str, required
        The name of the prefill meta.
    obligatorisk : bool, required
        Whether or not it is Required
    sti : Optional[str], default=None
        The path associated with the prefill meta.
    type : Optional[str], default="ORDINAR"
        The type of the prefill meta (e.g., "ORDINAR").
    min : Optional[int], default=None
        The minimum value allowed for the prefill meta.
    maks : Optional[int], default=None
        The maximum value allowed for the prefill meta.
    stat_navn : Optional[str], default=None
        The statistical name associated with the prefill meta.
    kommentar : Optional[str], default=None
        Any comments about the prefill meta.
    Returns:
    --------
    OperationResult:
        An object containing id of the new created prefill meta

    Example:
    ---------
    result = save_prefill_meta(
        skjema_id=123, min= 1, maks = 300, obligatorisk = True
    )
    """
    user = user_tools.get_current_user(context)

    model = SkjemaPrefillMetaRequestModel(
        skjema_id=skjema_id,
        navn=navn,
        sti=sti,
        type=type,
        min=min,
        maks=maks,
        obligatorisk=obligatorisk,
        dublett_sjekk=dublett_sjekk,
        stat_navn=stat_navn,
        kommentar=kommentar,
        endret_av=user,
    )

    try:
        body = model.model_dump_json()
        content: str = client.post(
            path=constants.PREFILL_META_PATH, body_json=body, context=context
        )
        new_id = json.loads(content)["id"]
        context.log(message="Created 'prefill meta' with new_id '{new_id}'")
        return OperationResult(value={"id": new_id}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to create prefill meta for skjema_id '{skjema_id}'",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=prefill_meta_id_validator)
def update_prefill_meta_by_prefill_meta_id(
    self,
    *,
    prefill_meta_id: int,
    obligatorisk: bool,
    skjema_id: Optional[int] | None = None,
    navn: Optional[str] | None = None,
    sti: Optional[str] | None = None,
    type: Optional[str] | None = None,
    min: Optional[int] | None = None,
    maks: Optional[int] | None = None,
    dublett_sjekk: Optional[bool] = None,
    stat_navn: Optional[str] | None = None,
    kommentar: Optional[str] | None = None,
    context: SuvOperationContext,
) -> OperationResult:
    """
    Updates prefill meta based on it's prefill_meta_id.

    Parameters:
    ------------
    prefill_meta_id: int, required
        The prefill_meta_id associated with the prefill meta.
    obligatorisk : bool, required
        Whether or not it is Required
    skjema_id : Optional[int], default=None
        The ID of the skjema associated with the prefill meta.
    navn : Optional[str], default=None
        The name of the prefill meta.
    sti : Optional[str], default=None
        The path associated with the prefill meta.
    type : Optional[str], default=None
        The type of the prefill meta (e.g., "ORDINAR").
    min : Optional[int], default=None
        The minimum value allowed for the prefill meta.
    maks : Optional[int], default=None
        The maximum value allowed for the prefill meta.
    stat_navn : Optional[str], default=None
        The statistical name associated with the prefill meta.
    kommentar : Optional[str], default=None
        Any comments about the prefill meta.

    Returns:
    --------
    OperationResult:
        An object containing updated prefill meta

    Example:
    ---------
    result = update_prefill_meta_by_prefill_meta_id(
        prefill_meta_id=123, min= 1, maks = 300, obligatorisk = True
    )
    """
    user = user_tools.get_current_user(context)
    prefill_meta = get_prefill_meta_by_prefill_meta_id(
        self=self, prefill_meta_id=prefill_meta_id
    )
    body = {
        "id": prefill_meta_id,
        "skjema_id": skjema_id or prefill_meta["skjema_id"],
        "navn": navn or prefill_meta["navn"],
        "sti": sti or prefill_meta["sti"],
        "type": type or prefill_meta["type"],
        "min": min or prefill_meta["min"],
        "maks": maks or prefill_meta["maks"],
        "obligatorisk": obligatorisk,
        "dublett_sjekk": dublett_sjekk
        if dublett_sjekk is not None
        else prefill_meta["dublett_sjekk"],
        "stat_navn": stat_navn or prefill_meta["stat_navn"],
        "kommentar": kommentar or prefill_meta["kommentar"],
        "endret_av": user,
    }

    try:
        body_json = json.dumps(body)
        content: str = client.put(
            path=f"{constants.PREFILL_META_PATH}/{prefill_meta_id}",
            body_json=body_json,
            context=context,
        )
        content_json = json.loads(content)
        context.log(message="Fetched 'prefill meta for prefill_meta_id '{skjema_id}'")
        return OperationResult(value=content_json, log=context.logs())

    except Exception as e:
        context.set_error(
            f"Failed to fetch prefill meta for prefill_meta_id {prefill_meta_id}", e
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=prefill_meta_id_validator)
def delete_skjema_prefill_meta_by_id(
    self, *, prefill_meta_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Deletes the prefill meta with the specified prefill_meta_id.

    Parameters:
    ------------
    prefill_meta_id: int
        The prefill_meta_id of the prefill meta to delete.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the result of the deletion operation, or an error message if the deletion fails.

    Example:
    ---------
    result = delete_skjema_prefill_meta_by_id(
        prefill_meta_id=123
    )
    """
    try:
        content: str = client.delete(
            path=f"{constants.PREFILL_META_PATH}/{prefill_meta_id}", context=context
        )
        context.log(
            message="Deleted 'skjema prefill meta' with prefill_meta_id '{prefill_meta_id}'"
        )
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to delete skjema prefill meta with prefill_meta_id '{prefill_meta_id}'.",
            e,
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=skjema_id_validator)
def delete_skjema_prefill_meta_by_skjema_id(
    self, *, skjema_id: int, context: SuvOperationContext
) -> OperationResult:
    """
    Deletes all prefill meta within the specified skjema_id.

    Parameters:
    ------------
    skjema_id: int
        The skjema_id of the prefill meta to delete.
    context: SuvOperationContext
        Operation context for logging and error handling. This is injected by the underlying pipeline.

    Returns:
    --------
    OperationResult:
        An object containing the result of the deletion operation, or an error message if the deletion fails.

    Example:
    ---------
    result = delete_skjema_prefill_meta_by_skjema_id(
        prefill_meta_id=123
    )
    """
    try:
        content: str = client.delete(
            path=f"{constants.PREFILL_META_PATH}/skjema/{skjema_id}", context=context
        )
        context.log(
            message="Deleted all 'skjema prefill meta' within skjema_id '{skjema_id}'"
        )
        return OperationResult(value={"result": content}, log=context.logs())
    except Exception as e:
        context.set_error(
            f"Failed to delete skjema prefill meta within skjema_id '{skjema_id}'.", e
        )
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
