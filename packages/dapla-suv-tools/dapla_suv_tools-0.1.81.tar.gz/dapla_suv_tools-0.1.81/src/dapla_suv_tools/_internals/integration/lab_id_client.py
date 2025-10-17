import requests
import json
from datetime import datetime, timezone
from dapla_suv_tools._internals.util.decorators import refresh_token_cache


class LabIdClient:
    cached_token: str
    last_cached: datetime
    refresh_interval: int

    def __init__(self):
        self.cached_token = ""
        self.last_cached = datetime.min
        self.refresh_interval = 600

    @refresh_token_cache
    def get_token(self):
        return self.cached_token

    @staticmethod
    def _get_lab_id_access_token() -> tuple[str, Exception | None]:
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
                kub_token = f.read()

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token_type": "urn:ietf:params:oauth:grant-type:id_token",
                "subject_token": kub_token,
                "scope": "current_group,all_groups",
                "audience": "suv-public-api",
            }

            response = requests.post(
                url="http://labid.labid.svc.cluster.local/token",
                headers=headers,
                data=data,
            )

            if response.status_code != 200:
                return "", Exception(response.text)

            json_response = json.loads(response.text)

            return json_response["access_token"], None
        except Exception as e:
            return "", e

    def refresh_token(self):
        time_since_last_cache = (
            datetime.now(tz=timezone.utc)
            - self.last_cached.replace(tzinfo=timezone.utc)
        ).seconds
        if self.cached_token == "" or time_since_last_cache > self.refresh_interval:
            self.cached_token, exception = self._get_lab_id_access_token()
            self.last_cached = datetime.now(tz=timezone.utc)

            if exception:
                print(f"Failed to get 'labId-token' with exception: {exception}")
