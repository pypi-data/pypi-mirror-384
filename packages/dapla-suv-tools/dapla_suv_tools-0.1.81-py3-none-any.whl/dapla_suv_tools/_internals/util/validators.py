import re
from datetime import date
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext


ra_pattern = re.compile("^[rR][aA]-[0-9]{4}(?:[aA]3)?$")

guid_pattern = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def instance_str_validator(ctx: SuvOperationContext, kwargs):
    instance_id = kwargs.get("instance_id", None)

    instance_owner_id = int(instance_id.split("/")[0])
    instance_guid = instance_id.split("/")[1]

    if not isinstance(instance_id, str):
        raise _set_error(
            ctx,
            "Parameter 'instance_id' must be a valid string. Eg. '123451213/12345678-1234-1234-1234-123456789012'",
        )

    if not re.match(guid_pattern, instance_guid):
        raise _set_error(
            ctx,
            "Guid for instance must match pattern 'xxxxxxxx-xxxx-vxxx-xxxx-xxxxxxxxxxxx' (x = digit 0-9, a-f)",
        )

    if not isinstance(instance_owner_id, int) or instance_owner_id == -1:
        raise _set_error(ctx, "Owner for instance must be a valid positive integer.")


def skjema_id_validator(ctx: SuvOperationContext, kwargs):
    skjema_id = kwargs.get("skjema_id", -1)

    if not isinstance(skjema_id, int) or skjema_id == -1:
        raise _set_error(ctx, "Parameter 'skjema_id' must be a valid positive integer.")


def prefill_meta_id_validator(ctx: SuvOperationContext, kwargs):
    prefill_meta_id = kwargs.get("prefill_meta_id", -1)

    if not isinstance(prefill_meta_id, int) or prefill_meta_id == -1:
        raise _set_error(
            ctx, "Parameter 'prefill_meta_id' must be a valid positive integer."
        )


def ra_update_validator(ctx: SuvOperationContext, kwargs):
    ra_nummer = kwargs.get("ra_nummer", None)
    versjon = kwargs.get("versjon", -1)
    undersokelse_nr = kwargs.get("undersokelse_nr", None)

    if not isinstance(ra_nummer, str):
        raise _set_error(ctx, "Parameter 'ra_nummer' must be a valid string.")

    if not re.match(ra_pattern, ra_nummer):
        raise _set_error(
            ctx,
            "Parameter 'ra_nummer' must match pattern 'ra-XXXX' or 'RA-XXXX' (X = digit 0-9)",
        )

    if not isinstance(versjon, int) or versjon == -1:
        raise _set_error(ctx, "Parameter 'versjon' must be a valid positive integer.")

    if not isinstance(undersokelse_nr, str):
        raise _set_error(ctx, "Parameter 'undersokelse_nr' must be a valid string.")


def pulje_id_validator(ctx: SuvOperationContext, kwargs):
    pulje_id = kwargs.get("pulje_id", -1)

    if not isinstance(pulje_id, int) or pulje_id == -1:
        raise _set_error(ctx, "Parameter 'pulje_id' must be a valid positive integer.")


def utsending_id_validator(ctx: SuvOperationContext, kwargs):
    pulje_id = kwargs.get("utsending_id", -1)

    if not isinstance(pulje_id, int) or pulje_id == -1:
        raise _set_error(
            ctx, "Parameter 'utsending_id' must be a valid positive integer."
        )


def ra_nummer_validator(ctx: SuvOperationContext, kwargs):
    ra_nummer = kwargs.get("ra_nummer", None)

    if not isinstance(ra_nummer, str):
        raise _set_error(ctx, "Parameter 'ra_nummer' must be a valid positive integer.")

    if not re.match(ra_pattern, ra_nummer):
        raise _set_error(
            ctx,
            "Parameter 'ra_nummer' must match pattern 'ra-XXXX' or 'RA-XXXX' (X = digit 0-9)",
        )


def ra_number_validator(ctx: SuvOperationContext, kwargs):
    ra_number = kwargs.get("ra_number", None)

    if not isinstance(ra_number, str):
        raise _set_error(ctx, "Parameter 'ra_number' must be a valid string.")

    if not re.match(ra_pattern, ra_number):
        raise _set_error(
            ctx,
            "Parameter 'ra_number' must match pattern 'ra-XXXX' or 'RA-XXXX' (X = digit 0-9)",
        )


def periode_id_validator(ctx: SuvOperationContext, kwargs):
    periode_id = kwargs.get("periode_id", -1)

    if not isinstance(periode_id, int) or periode_id == -1:
        raise _set_error(
            ctx, "Parameter 'periode_id' must be a valid positive integer."
        )


def delreg_id_validator(ctx: SuvOperationContext, kwargs):
    delreg_nr = kwargs.get("delreg_nr", -1)

    if not isinstance(delreg_nr, int) or delreg_nr == -1:
        raise _set_error(ctx, "Parameter 'delreg_nr' must be a valid positive integer.")


def _set_error(ctx: SuvOperationContext, message: str) -> Exception:
    ex = ValueError(message)
    ctx.set_error(error_msg=message, exception=ex)

    return ex
