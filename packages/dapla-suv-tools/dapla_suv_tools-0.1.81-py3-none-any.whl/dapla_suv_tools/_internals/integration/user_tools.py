import os

from dapla_auth_client import AuthClient

from dapla_suv_tools._internals.integration.lab_id_client import LabIdClient
from dapla_suv_tools._internals.util.suv_operation_context import SuvOperationContext
from dapla_suv_tools._internals.util import constants

lab_id_client = LabIdClient()


def get_access_token(context: SuvOperationContext) -> str:
    if os.getenv("LOCAL_DEV_ACTIVE", None):
        return os.getenv("SUV_LOCAL_TOKEN", "")

    context.log(level=constants.LOG_DIAGNOSTIC, message="Fetching user access_token")

    token = lab_id_client.get_token()

    if token:
        return token
    else:
        print("Unexpected response when fetching 'labId-token'.")
        context.log(
            level=constants.LOG_ERROR, message="Unexpected response from labId."
        )

    print("Attempting to fall back to default DaplaLab-token (OIDC_TOKEN).")

    return os.getenv("OIDC_TOKEN", "")


def get_current_user(context: SuvOperationContext) -> str:
    if os.getenv("LOCAL_DEV_ACTIVE", None):
        return os.getenv("SUV_LOCAL_USER", "")

    context.log(level=constants.LOG_DIAGNOSTIC, message="Fetching email")
    local_user = AuthClient.fetch_email_from_credentials()
    return local_user if local_user else "unknown"
