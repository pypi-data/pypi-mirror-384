import os


def build_prefill_api_url():
    if not END_USER_API_BASE_URL:
        return None
    return END_USER_API_BASE_URL.replace("-api.", "-prefill-api.")


OPERATION_OK = "OK"
OPERATION_ERROR = "ERROR"

LOG_DIAGNOSTIC = "diag"
LOG_INFO = "info"
LOG_WARNING = "warn"
LOG_ERROR = "error"

LOG_LEVELS = [LOG_DIAGNOSTIC, LOG_INFO, LOG_WARNING, LOG_ERROR]

# Not strictly constants, but will be constant, depending on runtime environment
END_USER_API_BASE_URL = os.getenv("SUV_DAPLA_API_URL", "")
PREFILL_API_BASE_URL = build_prefill_api_url()


def adjust_path(path: str) -> str:
    if END_USER_API_BASE_URL.endswith("/") and path.startswith("/"):
        return path[1:]
    return path


PERIODE_PATH = adjust_path("/periode")
PULJE_PATH = adjust_path("/pulje")
UTSENDING_PATH = adjust_path("/utsending")
UTSENDINGSTYPE_PATH = adjust_path("/utsendingstype")
SKJEMA_PATH = adjust_path("/skjemadata/skjema")
PREFILL_META_PATH = adjust_path("/skjemadata/prefill-meta")
INSTANCE_PATH = adjust_path("/altinn/instance")
INSTANTIATOR_RESEND_PATH = adjust_path("/instantiator/resend")
INNKVITTERING_RESEND_PATH = adjust_path("/innkvittering/resend")
PREFILL_API_STAT_PATH = adjust_path("/prefill")
SFU_PATH = adjust_path("/sfu/v2")
