import time
from unittest import TestCase
from unittest.mock import MagicMock

import freezegun
from pydantic import ValidationError
from settings_models.settings.common import Gate, GateType
from settings_models.settings.gate_control import GateMode

from openmodule.models.settings import SettingsChangedMessage
from openmodule.rpc import RPCServer, RPCClient
from openmodule.utils.settings import SettingsProvider
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.rpc import RPCServerTestMixin
from openmodule_test.settings import SettingsRPCMocker, SettingsMocker


# only gate_control/mode is scopes, so we use scoped2 as scoped for testing


class SettingsTestCase(OpenModuleCoreTestMixin, RPCServerTestMixin):
    def setUp(self) -> None:
        super().setUp()

        self.settings = SettingsProvider(rpc_timeout=1)
        self.rpc_server = RPCServer(self.zmq_context())
        self.settings_mocker = SettingsRPCMocker(self.rpc_server, {
            ("common/currency", ""): "EUR",
            ("common/gates", ""): {"1": {"gate": "1", "name": "2", "type": "exit"}},
            ("gate_control/mode", "1"): "automatic",
            ("scoped2", "1"): "test1",
            ("gate_control/mode", "2"): "standard",
            ("scoped2", "2"): "test1"}, allow_unknown_settings=True)
        self.rpc_server.run_as_thread()
        self.wait_for_rpc_server(self.rpc_server)

    def tearDown(self):
        self.rpc_server.shutdown()
        super().tearDown()

    def test_get(self):
        res = self.settings.get("common/gates")
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res)
        res = self.settings.get("gate_control/mode", "1")
        self.assertEqual(GateMode.automatic, res)
        res = self.settings.get("gate_control/mode", "2")
        self.assertEqual(GateMode.standard, res)
        self.settings.get("asdf", custom_type=str)

    def test_get_errors(self):
        res = self.settings.get("common/garage_name")
        self.assertIsNone(res)

        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.fail
        res = self.settings.get("common/gates")
        self.assertIsNone(res)

        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.error
        with self.assertRaises(RPCClient.ServerHandlerError):
            self.settings.get("common/gates")
        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.timeout
        with self.assertRaises(TimeoutError):
            self.settings.get("common/gates")

        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.fail
        self.settings_mocker.error_code = "i am an error"
        with self.assertLogs() as cm:
            self.assertIsNone(self.settings.get("common/gates"))
        self.assertIn("Settings RPC for key common/gates/ failed because of error i am an error",
                      str(cm.output))

    def test_get_cache(self):
        with freezegun.freeze_time("2020-01-01 00:00"):
            res = self.settings.get("common/gates")
            self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res)

            res = self.settings.get("gate_control/mode", "1")
            self.assertEqual(GateMode.automatic, res)

            self.settings_mocker.settings[("common/gates", "")] = {"2": {"gate": "2", "name": "3", "type": "entry"}}
            self.settings_mocker.settings[("gate_control/mode", "1")] = [{"data": "permanent_open"}]
            res = self.settings.get("common/gates")
            self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res)  # should use from cache

            # clear cache
            self.core.messages.dispatch("settings", SettingsChangedMessage(changed_keys=["common/gates/"]))
            res = self.settings.get("common/gates")
            self.assertEqual({"2": Gate(gate="2", name="3", type=GateType.entry)}, res)

            # key2 cache should not be cleared
            res = self.settings.get("gate_control/mode", "1")
            self.assertEqual(GateMode.automatic, res)

        self.settings_mocker.settings[("common/gates", "")] = {"3": {"gate": "3", "name": "4", "type": "entry"}}
        with freezegun.freeze_time("2020-01-01 00:04"):
            # cache should not be expired yet
            res = self.settings.get("common/gates")
            self.assertEqual({"2": Gate(gate="2", name="3", type=GateType.entry)}, res)  # should use from cache

        with freezegun.freeze_time("2020-01-01 00:06"):
            res = self.settings.get("common/gates")
            self.assertEqual({"3": Gate(gate="3", name="4", type=GateType.entry)}, res)

            self.settings_mocker.settings[("common/gates", "")] = ["test"]
            res = self.settings.get("common/gates", custom_type=list[str])
            self.assertEqual(["test"], res)

    def test_get_many(self):
        res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("EUR", res["common/currency"])
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res["common/gates"])

    def test_get_many_errors(self):
        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.first_fail
        res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertIsNone(res["common/currency"])
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res["common/gates"])

        # No cache exists
        self.settings_mocker.error_code = "i am an error"
        with self.assertLogs() as cm:
            res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")

        self.assertIsNone(res["common/currency"])
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res["common/gates"])
        self.assertIn("Failed to get setting common/currency/ because of error i am an error", str(cm.output))

        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.error
        with self.assertRaises(RPCClient.ServerHandlerError):
            self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.timeout
        with self.assertRaises(TimeoutError):
            self.settings.get_many({"common/currency": None, "common/gates": None}, "")

        self.settings_mocker.result_mode = SettingsRPCMocker.ResultMode.ok
        old_res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("EUR", old_res["common/currency"])
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, old_res["common/gates"])

        # Getting from cache
        self.settings_mocker.settings[("common/currency", "")] = "CHF"
        self.settings_mocker.settings[("common/gates", "")] = [{"gate": "2", "name": "3", "type": "entry"}]
        res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual(old_res, res)
        # Can't get from cache when parsing fails
        res = self.settings.get_many({"common/currency": None, "common/gates": list[Gate]}, "")
        self.assertNotEqual(old_res, res)
        self.assertEqual("CHF", res["common/currency"])
        self.assertEqual([Gate(gate="2", name="3", type=GateType.entry)], res["common/gates"])

        # Clear cache, create parsing error
        self.settings.settings_changed(SettingsChangedMessage(changed_keys=["common/gates/"]))
        res = self.settings.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("CHF", res["common/currency"])
        self.assertIsNone(res["common/gates"])

    def test_get_many_cache(self):
        with freezegun.freeze_time("2020-01-01 00:00"):
            old_res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "1")
            old_res_2 = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "2")

            # from cache
            self.settings_mocker.settings[("gate_control/mode", "1")] = "permanent_open"
            self.settings_mocker.settings[("scoped2", "1")] = "test2"
            res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "1")
            self.assertEqual(old_res, res)
            self.assertEqual(GateMode.automatic, res["gate_control/mode"])
            self.assertEqual("test1", res["scoped2"])

            # clear cache
            self.core.messages.dispatch("settings", SettingsChangedMessage(changed_keys=["gate_control/mode/1"]))
            # scoped2 still from cache
            res = self.settings.get_many({"scoped2": str}, "1")
            self.assertEqual(old_res["scoped2"], res["scoped2"])
            # scope "2" still from cache
            res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "2")
            self.assertEqual(old_res_2["gate_control/mode"], res["gate_control/mode"])
            self.assertEqual(old_res_2["scoped2"], res["scoped2"])
            # scope "1": all field new
            res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "1")
            self.assertNotEqual(old_res["gate_control/mode"], res["gate_control/mode"])
            self.assertNotEqual(old_res["scoped2"], res["scoped2"])
            self.assertEqual(GateMode.permanent_open, res["gate_control/mode"])
            self.assertEqual("test2", res["scoped2"])

        old_res = res
        self.settings_mocker.settings[("gate_control/mode", "1")] = "standard"
        self.settings_mocker.settings[("scoped2", "1")] = "test3"
        with freezegun.freeze_time("2020-01-01 00:04"):
            # cache should not be expired yet
            res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "1")
            self.assertEqual(old_res, res)
            self.settings._cached_values["scoped2/1"].expires_at = time.time() + 1000

        with freezegun.freeze_time("2020-01-01 00:06"):
            # cache should not be expired for req
            res = self.settings.get_many({"scoped2": str}, "1")
            self.assertEqual(old_res["scoped2"], res["scoped2"])

            # cache should be expired
            res = self.settings.get_many({"gate_control/mode": None, "scoped2": str}, "1")
            self.assertNotEqual(old_res["gate_control/mode"], res["gate_control/mode"])
            self.assertNotEqual(old_res["scoped2"], res["scoped2"])
            self.assertEqual(GateMode.standard, res["gate_control/mode"])
            self.assertEqual("test3", res["scoped2"])


class CustomSettingsTestCase(OpenModuleCoreTestMixin, RPCServerTestMixin):
    """
    The following tests can also show if the type hinting is working correctly. Rows that show an error have comments.
    Only known settings are allowed without a custom type.
    gate_control/mode needs to be called with a scope.
    ALL SETTINGS can be called with a custom type.
    """

    def setUp(self) -> None:
        super().setUp()
        self.settings = SettingsProvider(rpc_timeout=0.5)
        self.rpc_server = RPCServer(self.zmq_context())
        self.settings_mocker = SettingsRPCMocker(self.rpc_server, {
            ("common/gates", ""): [{"gate": "1", "name": "2", "type": "exit"},
                                   {"gate": "2", "name": "3", "type": "entry"}],
            ("unknown", ""): "test0",
            ("unknown/scoped", "1"): "test1",
            ("unknown/scoped", "2"): "test2",
            ("gate_control/mode", "1"): "automatic",
        }, allow_unknown_settings=True, allow_wrong_values=True)
        self.rpc_server.run_as_thread()
        self.wait_for_rpc_server(self.rpc_server)

    def test_unknown_setting(self):
        with self.assertRaises(KeyError) as e:
            self.settings.get("unknown")  # PyCharm should show Unexpected type
        self.assertEqual("'No model for setting unknown found'", str(e.exception))
        res = self.settings.get("unknown", custom_type=str)
        # PyCharm should NOT show Unexpected type
        self.assertEqual("test0", res)

        with self.assertRaises(KeyError) as e:
            self.settings.get("unknown/scoped", "1")  # PyCharm should show Unexpected type
        self.assertEqual("'No model for setting unknown/scoped found'", str(e.exception))
        res = self.settings.get("unknown/scoped", "1", custom_type=str)
        # PyCharm should NOT show Unexpected type
        self.assertEqual("test1", res)

    def test_missing_setting(self):
        # Known setting, but not set
        self.assertIsNone(self.settings.get("common/garage_name"))
        # Unknown setting, not set
        self.assertIsNone(self.settings.get("does/not/exist"))  # PyCharm should show Unexpected type

    def test_custom_type_for_known_setting(self):
        with self.assertRaises(ValidationError) as e:
            self.settings.get("common/gates")
        self.assertIn("1 validation error for dict[str,Gate]", str(e.exception))
        self.assertIn("Input should be a valid dictionary", str(e.exception))

        res = self.settings.get("common/gates", custom_type=list[Gate])
        self.assertEqual([Gate(gate="1", name="2", type=GateType.exit),
                          Gate(gate="2", name="3", type=GateType.entry)], res)

    def test_scope(self):
        self.assertIsNone(self.settings.get("gate_control/mode"))  # PyCharm should show Unexpected type
        res = self.settings.get("gate_control/mode", "1")
        self.assertEqual(GateMode.automatic, res)


class SettingsMockerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.rpc_server = MagicMock()

    def test_unknown_settings(self):
        with self.assertRaises(AssertionError) as e:
            SettingsRPCMocker(self.rpc_server, {("setting/test", ""): "test"})
        self.assertEqual("Unknown setting setting/test", str(e.exception))
        mocker = SettingsRPCMocker(self.rpc_server, {("setting/test", ""): "test"}, allow_unknown_settings=True)
        self.assertEqual("test", mocker.settings[("setting/test", "")])

        with self.assertRaises(AssertionError) as e:
            SettingsMocker({("setting/test", ""): "test"})
        self.assertEqual("Unknown setting setting/test", str(e.exception))
        mocker = SettingsMocker({("setting/test", ""): "test"}, allow_unknown_settings=True)
        self.assertEqual("test", mocker.settings[("setting/test", "")])

        res = mocker.get("setting/test")
        self.assertIsNone(res)
        res = mocker.get("setting/test", custom_type=str)
        self.assertEqual("test", res)

    def test_wrong_values(self):
        with self.assertRaises(ValidationError) as e:
            SettingsRPCMocker(self.rpc_server, {("common/garage_name", ""): {"parkinglot_name": "test"}})
        self.assertIn("3 validation errors for GarageName\n", str(e.exception))
        self.assertIn("name\n", str(e.exception))
        self.assertIn("technical_name\n", str(e.exception))
        self.assertIn("slug\n", str(e.exception))


        mocker = SettingsRPCMocker(
            self.rpc_server,
            {("common/garage_name", ""): {"parkinglot_name": "test"}},
            allow_wrong_values=True
        )
        self.assertEqual({"parkinglot_name": "test"}, mocker.settings[("common/garage_name", "")])

        with self.assertRaises(ValidationError) as e:
            SettingsMocker({("common/garage_name", ""): {"parkinglot_name": "test"}})
        self.assertIn("3 validation errors for GarageName\n", str(e.exception))
        self.assertIn("name\n", str(e.exception))
        self.assertIn("technical_name\n", str(e.exception))
        self.assertIn("slug\n", str(e.exception))

        mocker = SettingsMocker({("common/garage_name", ""): {"parkinglot_name": "test"}}, allow_wrong_values=True)
        self.assertEqual({"parkinglot_name": "test"}, mocker.settings[("common/garage_name", "")])

    def test_settings_mocker(self):
        mocker = SettingsMocker({("common/currency", ""): "EUR",
                                 ("common/gates", ""): {"1": {"gate": "1", "name": "2", "type": "exit"}}})
        res = mocker.get("common/currency")
        self.assertEqual("EUR", res)

        res = mocker.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("EUR", res["common/currency"])
        self.assertEqual({"1": Gate(gate="1", name="2", type=GateType.exit)}, res["common/gates"])

        mocker.change_setting("CHF", "common/currency")
        mocker.remove_setting("common/gates")
        res = mocker.get("common/gates")
        self.assertIsNone(res)
        res = mocker.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("CHF", res["common/currency"])
        self.assertIsNone(res["common/gates"])

        mocker.add_setting("en", "common/language")
        res = mocker.get("common/language")
        self.assertEqual("en", res)

    def test_settings_mocker_scoped(self):
        mocker = SettingsMocker({("gate_control/mode", "1"): "automatic",
                                 ("scoped2", "1"): "test1",
                                 ("gate_control/mode", "2"): "standard"}, allow_unknown_settings=True)
        res = mocker.get("gate_control/mode")
        self.assertIsNone(res)

        res = mocker.get("gate_control/mode", "1")
        self.assertEqual(GateMode.automatic, res)
        res = mocker.get("scoped2", "1", custom_type=str)
        self.assertEqual("test1", res)
        res = mocker.get("gate_control/mode", "2")
        self.assertEqual(GateMode.standard, res)

        res = mocker.get_many({"gate_control/mode": None, "scoped2": str}, "1")
        self.assertEqual(GateMode.automatic, res["gate_control/mode"])
        self.assertEqual("test1", res["scoped2"])

        res = mocker.get_many({"gate_control/mode": None, "scoped2": str}, "2")
        self.assertEqual(GateMode.standard, res["gate_control/mode"])
        self.assertIsNone(res["scoped2"])

        mocker.change_setting("permanent_open", "gate_control/mode", "1")
        mocker.remove_setting("scoped2", "1")
        res = mocker.get("scoped2", "1", custom_type=str)
        self.assertIsNone(res)
        res = mocker.get_many({"gate_control/mode": None, "scoped2": str}, "1")
        self.assertEqual(GateMode.permanent_open, res["gate_control/mode"])
        self.assertIsNone(res["scoped2"])

    def test_settings_mocker_errors(self):
        mocker = SettingsMocker({("common/currency", ""): "EUR",
                                 ("common/gates", ""): {"1": {"gate": "1", "name": "2", "type": "exit"}}})
        mocker.exception = Exception("test")
        with self.assertRaises(Exception) as e:
            mocker.get("common/currency")
        self.assertEqual("test", str(e.exception))

        with self.assertRaises(Exception) as e:
            mocker.get_many({"common/currency": None, "common/gates": None}, "")
        self.assertEqual("test", str(e.exception))
