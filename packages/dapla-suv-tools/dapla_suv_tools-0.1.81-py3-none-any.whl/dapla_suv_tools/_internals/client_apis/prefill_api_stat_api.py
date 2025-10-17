from typing import Optional, Any
import json

from dapla_suv_tools._internals.integration.api_client import SuvApiClient
from dapla_suv_tools._internals.util.decorators import result_to_dict
from dapla_suv_tools._internals.util.operation_result import OperationResult
import dapla_suv_tools._internals.util.constants as constants
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util.validators import ra_nummer_validator


client = SuvApiClient(base_url=constants.PREFILL_API_BASE_URL)


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def get_prefill_info_for_skjema(
        self,
        *,
        ra_nummer: str,
        versjon: int,
        periode_aar: int,
        periode_type: str,
        periode_nr: Optional[int],
        context: SuvOperationContext
) -> OperationResult:
    """
    Fetches prefill information for a given combination of skjema-identifiers and periode-identifiers.

    :param ra_nummer: str, required  Ra-number of the skjema
    :param versjon:  int, required   Version indicator of the skjema
    :param periode_aar: int, required  The year of the period
    :param periode_type: str, required  The type of period
    :param periode_nr: int, optional   The number of the period.  Not required for annual surveys.
    :param context:
    :return:
    """
    try:
        query = f"ra_nummer={ra_nummer}&versjon={versjon}&periode_aar={periode_aar}&periode_type={periode_type}"
        if periode_nr:
            query += f"&periode_nummer={periode_nr}"
        
        content = client.get(path=f"{constants.PREFILL_API_STAT_PATH}/skjema?{query}", context=context)
        content_json = json.loads(content)
        context.log(message=f"Fetched prefill-info for: {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}")
        return OperationResult(
            value=content_json, log=context.logs()
        )
    except Exception as e:
        context.set_error(f"Failed to fetch for {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def get_prefill_for_enhet(
        self,
        *,
        ra_nummer: str,
        versjon: int,
        periode_aar: int,
        periode_type: str,
        periode_nr: Optional[int],
        enhetsident: str,
        enhetstype: str,
        context: SuvOperationContext
) -> OperationResult:
    """
    Fetches prefill for a given unit for a combination of skjema-identifiers and periode-identifiers.

    :param ra_nummer: str, required  Ra-number of the skjema
    :param versjon:  int, required   Version indicator of the skjema
    :param periode_aar: int, required  The year of the period
    :param periode_type: str, required  The type of period
    :param periode_nr: int, optional   The number of the period.  Not required for annual surveys.
    :param enhetsident: str, required  An identifier for the unit
    :param enhetstype: str, required   Type indicator for the unit
    :param context:
    :return:
    """
    try:
        query = f"ra_nummer={ra_nummer}&versjon={versjon}&periode_aar={periode_aar}&periode_type={periode_type}"
        if periode_nr:
            query += f"&periode_nummer={periode_nr}"
        query += f"&enhetsident={enhetsident}&enhetstype={enhetstype}"
        content = client.get(path=f"{constants.PREFILL_API_STAT_PATH}/skjema/enhet?{query}", context=context)
        content_json = json.loads(content)
        context.log(message=f"Fetched prefill for enhet {enhetsident}-{enhetstype}:  {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}")
        return OperationResult(
            value=content_json, log=context.logs()
        )
    except Exception as e:
        context.set_error(f"Failed to fetch for enhet {enhetsident}-{enhetstype}: {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def delete_prefill_for_skjema(
        self,
        *,
        ra_nummer: str,
        versjon: int,
        periode_aar: int,
        periode_type: str,
        periode_nr: Optional[int],
        context: SuvOperationContext
) -> OperationResult:
    """
    Deletes all prefill information for a given combination of skjema-identifiers and periode-identifiers.
    This operation is not reversible, and can not be undone!!

    :param ra_nummer: str, required  Ra-number of the skjema
    :param versjon:  int, required   Version indicator of the skjema
    :param periode_aar: int, required  The year of the period
    :param periode_type: str, required  The type of period
    :param periode_nr: int, optional   The number of the period.  Not required for annual surveys.
    :param context:
    :return:
    """
    try:
        query = f"ra_nummer={ra_nummer}&versjon={versjon}&periode_aar={periode_aar}&periode_type={periode_type}"
        if periode_nr:
            query += f"&periode_nummer={periode_nr}"
        content = client.delete(path=f"{constants.PREFILL_API_STAT_PATH}/skjema?{query}", context=context)
        content_json = json.loads(content)
        context.log(message=f"Deleted prefill for skjema {ra_nummer}-{versjon}: {content_json['entries_deleted']} rows ({content_json['message']})")
        return OperationResult(
            value=content_json, log=context.logs()
        )
    except Exception as e:
        context.set_error(f"Failed to delete for skjema {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def delete_prefill_for_enhet(
        self,
        *,
        ra_nummer: str,
        versjon: int,
        periode_aar: int,
        periode_type: str,
        periode_nr: Optional[int],
        enhetsident: str,
        enhetstype: str,
        context: SuvOperationContext
) -> OperationResult:
    """
    Deletes prefill for a given unit for a combination of skjema-identifiers and periode-identifiers.
    This operation is not reversible, and can not be undone!!

    :param ra_nummer: str, required  Ra-number of the skjema
    :param versjon:  int, required   Version indicator of the skjema
    :param periode_aar: int, required  The year of the period
    :param periode_type: str, required  The type of period
    :param periode_nr: int, optional   The number of the period.  Not required for annual surveys.
    :param enhetsident: str, required  An identifier for the unit
    :param enhetstype: str, required   Type indicator for the unit
    :param context:
    :return:
    """
    try:
        query = f"ra_nummer={ra_nummer}&versjon={versjon}&periode_aar={periode_aar}&periode_type={periode_type}"
        if periode_nr:
            query += f"&periode_nummer={periode_nr}"
        query += f"&enhetsident={enhetsident}&enhetstype={enhetstype}"
        content = client.delete(path=f"{constants.PREFILL_API_STAT_PATH}/skjema/enhet?{query}", context=context)
        content_json = json.loads(content)
        context.log(message=f"Deleted prefill for enhet {enhetsident}-{enhetstype}: {content_json['entries_deleted']} rows ({content_json['message']})")
        return OperationResult(
            value=content_json, log=context.logs()
        )
    except Exception as e:
        context.set_error(f"Failed to delete for enhet {enhetsident}-{enhetstype}: {ra_nummer}-{versjon} ({periode_aar}-{periode_type}-{periode_nr}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def save_prefill_for_enhet(
        self,
        *,
        ra_nummer: str,
        versjon: int,
        periode_aar: int,
        periode_type: str,
        periode_nr: Optional[int],
        enhetsident: str,
        enhetstype: str,
        prefill: dict[str, Any],
        context: SuvOperationContext
) -> OperationResult:
    """
    Saves prefill for a given unit for a combination of skjema-identifiers and periode-identifiers.
    This will overwrite any registered prefill for the unit for the given survey!!  This action is not
    reversible, and can not be undone!!

    :param ra_nummer: str, required  Ra-number of the skjema
    :param versjon:  int, required   Version indicator of the skjema
    :param periode_aar: int, required  The year of the period
    :param periode_type: str, required  The type of period
    :param periode_nr: int, optional   The number of the period.  Not required for annual surveys.
    :param enhetsident: str, required  An identifier for the unit
    :param enhetstype: str, required   Type indicator for the unit
    :param prefill: dict, required   A dictionary (json-object) containing the prefill information for the unit.
    :param context:
    :return:
    """
    try:
        prefill_json_string = json.dumps(prefill)

        data = {
            "ra_nummer": ra_nummer,
            "versjon": versjon,
            "periode_aar": periode_aar,
            "periode_type": periode_type,
            "periode_nummer": periode_nr,
            "enhetsident": enhetsident,
            "enhetstype": enhetstype,
            "prefill": prefill_json_string
        }
        result = client.post(path=f"{constants.PREFILL_API_STAT_PATH}/skjema/enhet", body_json=json.dumps(data), context=context)
        result_json = json.loads(result)

        context.log(message=f"Added prefill for enhet: {enhetsident} - {enhetstype}")
        return OperationResult(value=result_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Failed to add preffill for enhet {enhetsident}-{enhetstype}", e)

        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )


@result_to_dict
@SuvOperationContext(validator=ra_nummer_validator)
def validate_skjemadata(
        self,
        *,
        skjemadata: dict,
        ra_nummer: str,
        versjon: int,
        context: SuvOperationContext
) -> OperationResult:
    """
    Validates skjemadata for a given unit for a combination of skjema-identifiers.
    
    :param skjemadata: str, required  skjemadata 
    :param ra_nummer: str, required  Ra-number 
    :param versjon:  int, required   Version 

    :param context:
    :return:
    """
    versjon=str(versjon)

    try:
        skjemadata_str = json.dumps(skjemadata)

        # Manually URL-encode 
        def simple_url_encode(s: str) -> str:
            encoded = []
            for ch in s:
                # These are the "unreserved" characters in URLs:
                if ch.isalnum() or ch in ['-', '_', '.', '~']:
                    encoded.append(ch)
                else:
                    encoded.append('%{:02X}'.format(ord(ch)))
            return ''.join(encoded)

        skjemadata_encoded = simple_url_encode(skjemadata_str)
        url = (
            f"{constants.PREFILL_API_STAT_PATH}/validate/skjemadata/"
            f"{ra_nummer}/{versjon}?skjemadata={skjemadata_encoded}"
        )
        result = client.post(path=url, body_json={}, context=context)
        result_json = json.loads(result)

        context.log(message=f"result: {result_json}")
        return OperationResult(value=result_json, log=context.logs())
    except Exception as e:
        context.set_error(f"Error validating skjemadata by {ra_nummer} v{versjon}", e)
        return OperationResult(
            success=False, value=context.errors(), log=context.logs()
        )
