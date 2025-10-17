from typing import Callable, Optional
from dapla_suv_tools._internals.util.help_helper import HelpAssistant
from dapla_suv_tools._internals.util import constants


class SuvClient:
    suppress_exceptions: bool
    operations_log: list
    help_assistant: HelpAssistant

    from dapla_suv_tools._internals.client_apis.skjema_api import (
        get_skjema_by_id,
        get_skjema_by_ra_nummer,
        create_skjema,
        delete_skjema,
        update_skjema_by_ra_number,
        update_skjema_by_id,
        get_all_skjema,
    )

    from dapla_suv_tools._internals.client_apis.periode_api import (
        get_periode_by_id,
        get_perioder_by_skjema_id,
        create_periode,
        delete_periode,
        update_periode_by_id,
        update_periode_by_skjema_id,
        create_new_periodes,
    )

    from dapla_suv_tools._internals.client_apis.pulje_api import (
        get_pulje_by_id,
        get_pulje_by_periode_id,
        create_pulje,
        update_pulje_by_id,
        update_pulje_by_periode_id,
        delete_pulje,
    )
    from dapla_suv_tools._internals.client_apis.utsending_api import (
        get_utsending_by_id,
        get_utsending_by_pulje_id,
        update_utsending_by_id,
        create_utsending,
        delete_utsending,
    )

    from dapla_suv_tools._internals.client_apis.sfu_api import (
        get_utvalg_from_sfu,
        get_enhet_from_sfu,
        get_vareliste,
        get_prefill_isee,
    )

    from dapla_suv_tools._internals.client_apis.instans_api import (
        get_instance,
    )

    from dapla_suv_tools._internals.client_apis.instantiator_api import (
        resend_instances,
    )

    from dapla_suv_tools._internals.client_apis.innkvittering_api import (
        resend_receipts,
    )

    from dapla_suv_tools._internals.client_apis.prefill_meta_api import (
        get_prefill_meta_by_skjema_id,
        get_prefill_meta_by_skjema_def,
        save_prefill_meta,
        get_prefill_meta_by_prefill_meta_id,
        update_prefill_meta_by_prefill_meta_id,
        delete_skjema_prefill_meta_by_id,
        delete_skjema_prefill_meta_by_skjema_id,
    )

    from dapla_suv_tools._internals.client_apis.prefill_api_stat_api import (
        get_prefill_info_for_skjema,
        get_prefill_for_enhet,
        save_prefill_for_enhet,
        delete_prefill_for_skjema,
        delete_prefill_for_enhet,
        validate_skjemadata,
    )

    def __init__(self, suppress_exceptions: bool = False):
        self.suppress_exceptions = suppress_exceptions
        self.operations_log = []
        self._build_help_cache()

    def logs(self, threshold: str | None = None, results: int = 0) -> list:
        if not threshold or threshold not in constants.LOG_LEVELS:
            threshold = constants.LOG_INFO

        log = self._filter_logs(threshold=threshold)

        if results > 0:
            return log[-results:]

        return log

    def help(self, function: Optional[Callable] = None):
        if function is None:
            return self.__doc__
        doc = self.help_assistant.get_function_help_entry(function.__name__)

        if doc is not None:
            print(doc)

        print(f"No help entry for '{function.__name__}' exists.")

    def _build_help_cache(self):
        self.help_assistant = HelpAssistant()
        self.help_assistant.register_functions(
            [
                self.get_skjema_by_id,
                self.get_skjema_by_ra_nummer,
                self.create_skjema,
                self.delete_skjema,
                self.get_periode_by_id,
                self.get_perioder_by_skjema_id,
                self.create_periode,
                self.delete_periode,
                self.update_skjema_by_ra_number,
                self.update_skjema_by_id,
                self.get_all_skjema,
                self.update_periode_by_id,
                self.update_periode_by_skjema_id,
                self.get_pulje_by_id,
                self.get_pulje_by_periode_id,
                self.create_pulje,
                self.update_pulje_by_id,
                self.update_pulje_by_periode_id,
                self.delete_pulje,
                self.get_utsending_by_id,
                self.get_utsending_by_pulje_id,
                self.update_utsending_by_id,
                self.create_utsending,
                self.delete_utsending,
                self.get_instance,
                self.resend_instances,
                self.resend_receipts,
                self.get_prefill_meta_by_skjema_id,
                self.get_prefill_info_for_skjema,
                self.get_prefill_for_enhet,
                self.save_prefill_for_enhet,
                self.delete_prefill_for_skjema,
                self.delete_prefill_for_enhet,
                self.get_utvalg_from_sfu,
                self.get_enhet_from_sfu,
                self.get_vareliste,
                self.get_prefill_isee,
                self.validate_skjemadata,
                self.get_prefill_meta_by_skjema_def,
                self.save_prefill_meta,
                self.get_prefill_meta_by_prefill_meta_id,
                self.update_prefill_meta_by_prefill_meta_id,
                self.delete_skjema_prefill_meta_by_id,
                self.delete_skjema_prefill_meta_by_skjema_id,
                self.create_new_periodes,
            ]
        )

    def flush_logs(self):
        self.operations_log = []

    def _filter_logs(self, threshold: str) -> list:
        limit = constants.LOG_LEVELS.index(threshold)

        filtered = []

        for log_entry in self.operations_log:
            logs = log_entry["logs"]
            if len(logs) == 0:
                continue
            for entry in logs:
                if constants.LOG_LEVELS.index(entry["level"]) < limit:
                    continue
                filtered.append(entry)

        return sorted(filtered, key=lambda x: x["time"])
