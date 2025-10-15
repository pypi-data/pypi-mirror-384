import logging
import threading
import time
from typing import Any, TypeVar, Literal, overload

from settings_models.serialization import parse_setting_from_obj
from settings_models.settings.common import GarageName, Gates, Rates, ParkingAreas, Parksettings, PrivacySettings, \
    CostGroups, GarageSettings, Location, BillingSettings, SupportSettings, Urls
from settings_models.settings.device_keys import PairingKey, Certificate, Otp
from settings_models.settings.enforcement import EnforcementSettings
from settings_models.settings.gate_control import GateMode, DayMode
from settings_models.settings.intercom import IntercomSettings
from settings_models.settings.io import SignalDefinitions, InputDefinitions

from openmodule import sentry
from openmodule.core import core
from openmodule.models.settings import SettingsChangedMessage, SettingsGetRequest, SettingsGetResponse, \
    SettingsGetManyRequest, SettingsGetManyResponse

# Should be not None, but this feature does not exist
T = TypeVar("T")


def join_key(key, scope):
    return f"{key}/{scope}"


class CachedSetting:
    def __init__(self, value: Any, expires_at: float):
        self.expires_at = expires_at
        self.value = value

    def is_expired(self):
        return time.time() > self.expires_at


class SettingsProvider:
    _cached_values: dict[str, CachedSetting]

    def __init__(self, expire_time=300.0, rpc_timeout=3.0):
        self.log = logging.getLogger(__name__)
        self.expire_time = expire_time
        self.rpc_timeout = rpc_timeout
        self._cached_values = {}
        self._cache_lock = threading.Lock()
        core().messages.register_handler("settings", SettingsChangedMessage, self.settings_changed)

    def settings_changed(self, message: SettingsChangedMessage):
        """
        invalidate cached settings when changed
        """
        with self._cache_lock:
            for key in message.changed_keys:
                self._cached_values.pop(key, None)

    @sentry.trace
    def _get_rpc(self, key: str, scope: str = "", custom_type: type[T] | None = None) -> T | None:
        key_scope = join_key(key, scope)
        with self._cache_lock:
            self._cached_values.pop(key_scope, None)
        response = core().rpc_client.rpc("settings", "get", SettingsGetRequest(key=key, scope=scope),
                                         SettingsGetResponse, self.rpc_timeout)

        if not response.success:
            if response.error != "no such setting":
                self.log.error(f"Settings RPC for key {key_scope} failed because of error {response.error}")
            return None
        result = parse_setting_from_obj(key, response.value, custom_type)
        with self._cache_lock:
            self._cached_values[key_scope] = CachedSetting(response.value, time.time() + self.expire_time)
        return result

    @sentry.trace
    def _get_many_rpc(self, keys_with_types: dict[str, type[T] | None], scope: str = "") -> dict[str, Any]:
        with self._cache_lock:
            for key in keys_with_types.keys():
                self._cached_values.pop(join_key(key, scope), None)
        response = core().rpc_client.rpc("settings", "get_many",
                                         SettingsGetManyRequest(key=list(keys_with_types.keys()), scope=scope),
                                         SettingsGetManyResponse, self.rpc_timeout)
        results = {}
        for key, setting in response.settings.items():
            key_scope = join_key(key, scope)
            if not setting.success:
                if setting.error != "no such setting":
                    self.log.error(f"Failed to get setting {key_scope} because of error {setting.error}")
                results[key] = None
                continue
            try:
                result = parse_setting_from_obj(key, setting.value, keys_with_types[key])
            except Exception:
                self.log.error(f"Failed to parse setting {key_scope}")
                results[key] = None
                continue
            results[key] = result
            with self._cache_lock:
                self._cached_values[key_scope] = CachedSetting(setting.value, time.time() + self.expire_time)
        return results

    @overload
    def get(self, key: str, custom_type: type[T]) -> T | None:  # pragma: no cover
        ...

    @overload
    def get(self, key: str, scope: str, custom_type: type[T]) -> T | None:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/gates"]) -> Gates:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/rates"]) -> Rates:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/parking_areas2"]) -> ParkingAreas:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/parksettings2"]) -> Parksettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/privacy_settings"]) -> PrivacySettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/cost_groups"]) -> CostGroups:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/currency"]) -> str:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/language"]) -> str:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/timezone"]) -> str:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/garage_settings"]) -> GarageSettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/location"]) -> Location:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/billing"]) -> BillingSettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/support"]) -> SupportSettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/garage_name"]) -> GarageName:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["common/urls"]) -> Urls:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["gate_control/mode"], scope: str) -> GateMode:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["gate_control/day_mode"]) -> DayMode:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["enforcement/basic_settings"]) -> EnforcementSettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["intercom/basic_settings"]) -> IntercomSettings:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["device_keys/pairing"]) -> PairingKey:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["device_keys/cert"]) -> Certificate:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["device_keys/otp"]) -> Otp:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["feature_flags"]) -> dict:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["io/signals"]) -> SignalDefinitions:  # pragma: no cover
        ...

    @overload
    def get(self, key: Literal["io/inputs"]) -> InputDefinitions:  # pragma: no cover
        ...

    def get(self, key: str, scope: str = "", custom_type: type[T] | None = None) -> T | None:
        key_scope = join_key(key, scope)
        with self._cache_lock:
            if key_scope in self._cached_values:
                if self._cached_values[key_scope].is_expired():
                    self._cached_values.pop(key_scope, None)
                else:
                    try:
                        return parse_setting_from_obj(
                            key, self._cached_values[key_scope].value, custom_type)
                    except Exception:
                        self.log.error("Tried to get same settings with different incompatible types")
                        self._cached_values.pop(key_scope, None)
        return self._get_rpc(key, scope, custom_type)

    def get_many(self, keys_with_types: dict[str, type[T] | None], scope: str = "") -> dict[str, T]:
        all_found_in_cache = True
        results = {}
        with self._cache_lock:
            for key, custom_type in keys_with_types.items():
                key_scope = join_key(key, scope)
                if key_scope in self._cached_values:
                    if self._cached_values[key_scope].is_expired():
                        self._cached_values.pop(key_scope, None)
                        all_found_in_cache = False
                    else:
                        try:
                            results[key] = parse_setting_from_obj(
                                key, self._cached_values[key_scope].value, custom_type)
                        except Exception:
                            self.log.error("Tried to get same settings with different incompatible types")
                            self._cached_values.pop(key_scope, None)
                            all_found_in_cache = False
                else:
                    all_found_in_cache = False
        if all_found_in_cache:
            return results
        else:
            return self._get_many_rpc(keys_with_types, scope)
