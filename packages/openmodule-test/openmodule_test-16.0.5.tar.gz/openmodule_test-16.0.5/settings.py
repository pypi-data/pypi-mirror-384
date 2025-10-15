import time
from enum import StrEnum
from typing import Any, TypeVar

from settings_models import serialization

from openmodule.models.settings import SettingsGetRequest, SettingsGetResponse, SettingsGetManyRequest, \
    SettingsGetManyResponse
from openmodule.rpc import RPCServer

T = TypeVar('T')


class SettingsMocker:
    """
    easy settings mock: replace SettingsProvider with SettingsMocker
    put your settings into mocker as (<key>, <scope>): <setting>
    to allow settings that are not defined in the settings model, set allow_unknown_settings to True
    to allow values that would not parse the default settings models, set allow_wrong_values to True
    """

    # noinspection PyMissingConstructor
    def __init__(self, settings: dict[tuple[str, str], Any],
                 allow_unknown_settings: bool = False, allow_wrong_values: bool = False):
        if not allow_unknown_settings:
            for setting in settings:
                assert setting[0] in serialization._model_mapping, f"Unknown setting {setting[0]}"
        if not allow_wrong_values:
            for setting, value in settings.items():
                if setting[0] in serialization._model_mapping:
                    serialization.parse_setting_from_obj(setting[0], value)
        self.settings = settings
        self.exception = None

    def get(self, key: str, scope: str = "", custom_type: type[T] | None = None) -> T | None:
        if self.exception:
            raise self.exception
        value = self.settings.get((key, scope))
        if value is None:
            return None
        try:
            return serialization.parse_setting_from_obj(key, self.settings.get((key, scope)), custom_type)
        except Exception:
            return None

    def get_many(self, keys_with_types: dict[str, type[T]], scope: str = "") -> dict[str, T]:
        if self.exception:
            raise self.exception
        else:
            return {key: self.get(key, scope, custom_type) for key, custom_type in keys_with_types.items()}

    def add_setting(self, value: Any, key: str, scope: str = ""):
        self.change_setting(value, key, scope)

    def change_setting(self, value: Any, key: str, scope: str = ""):
        self.settings[(key, scope)] = value

    def remove_setting(self, key: str, scope: str = ""):
        self.settings.pop((key, scope), None)


class SettingsRPCMocker:
    """
    settings mocker which answers RPCs: Useful when replacing SettingsProvider is not possible
    (e.g. when testing a subclass of SettingsProvider)
    put your settings into mocker as (<key>, <scope>): <setting>
    to allow settings that are not defined in the settings model, set allow_unknown_settings to True
    to allow values that would not parse the default settings models, set allow_wrong_values to True
    use result_mode to simulate errors
    """

    class ResultMode(StrEnum):
        ok = "ok"  # successful
        error = "error"  # raise error in callback
        timeout = "timeout"  # sleep in callback for 1 second
        fail = "fail"  # return success false
        first_fail = "first_fail"  # return success false for first in get_many

    def __init__(self, rpc_server: RPCServer, settings: dict[tuple[str, str], Any],
                 allow_unknown_settings: bool = False, allow_wrong_values: bool = False):
        if not allow_unknown_settings:
            for setting in settings:
                assert setting[0] in serialization._model_mapping, f"Unknown setting {setting[0]}"
        if not allow_wrong_values:
            for setting, value in settings.items():
                if setting[0] in serialization._model_mapping:
                    serialization.parse_setting_from_obj(setting[0], value)
        rpc_server.register_handler("settings", "get", SettingsGetRequest, SettingsGetResponse, self._get_handler)
        rpc_server.register_handler("settings", "get_many", SettingsGetManyRequest, SettingsGetManyResponse,
                                    self._get_many_handler)
        self.settings = settings
        self.result_mode = SettingsRPCMocker.ResultMode.ok
        self.error_code = "no such setting"

    def _get_setting(self, key, scope, idx=0) -> SettingsGetResponse:
        setting = self.settings.get((key, scope))
        if setting is None or self.result_mode == SettingsRPCMocker.ResultMode.fail or \
                (idx == 0 and self.result_mode == SettingsRPCMocker.ResultMode.first_fail):
            return SettingsGetResponse(success=False, error=self.error_code)
        else:
            return SettingsGetResponse(value=setting, success=True)

    def _do_errors(self):
        if self.result_mode == SettingsRPCMocker.ResultMode.error:
            raise RuntimeError()
        elif self.result_mode == SettingsRPCMocker.ResultMode.timeout:
            time.sleep(1)
            raise RuntimeError()

    def _get_handler(self, request: SettingsGetRequest, _) -> SettingsGetResponse:
        """ either raise set error or return requested value """
        self._do_errors()
        return self._get_setting(request.key, request.scope)

    def _get_many_handler(self, request: SettingsGetManyRequest, _) -> SettingsGetManyResponse:
        """ either raise set error or return requested values """
        self._do_errors()
        return SettingsGetManyResponse(settings={key: self._get_setting(key, request.scope, i)
                                                 for i, key in enumerate(request.key)})
