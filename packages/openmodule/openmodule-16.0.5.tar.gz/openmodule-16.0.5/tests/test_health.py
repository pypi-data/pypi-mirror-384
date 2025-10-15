from unittest import TestCase

from openmodule.config import override_settings, override_context
from openmodule.core import init_openmodule, shutdown_openmodule
from openmodule.health import HealthMetricType, HealthPongMessage
from openmodule_test.health import HealthTestMixin


class HealthTestCase(HealthTestMixin, TestCase):
    topics = ["healthpong"]

    def setUp(self):
        super().setUp()
        self.core = init_openmodule(context=self.zmq_context(), config=self.zmq_config())
        self.addCleanup(shutdown_openmodule)
        self.wait_for_health()

    def tearDown(self):
        super().tearDown()

    def test_health_is_answering(self):
        health = self.get_health()
        self.assertEqual(health["pong"]["status"], "ok")

    def test_status_and_message(self):
        self.core.health.add_check("test", "Test", "for testing")
        self.core.health.add_check("test2", "Test2", "another for testing")
        health = self.get_health()
        self.assertEqual(health["pong"]["status"], "ok")
        self.core.health.check_fail("test2", message="error2")
        health = self.get_health()
        self.assertEqual(health["pong"]["status"], "error")
        self.assertEqual(health["pong"]["message"], "error2")
        self.core.health.check_success("test2")
        self.core.health.check_fail("test", message="error")
        health = self.get_health()
        self.assertEqual(health["pong"]["status"], "error")
        self.assertEqual(health["pong"]["message"], "error")

    def test_metrics(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing",
                                    labels={"lc1", "lc2"})
        self.core.health.add_metric("test_str", HealthMetricType.str, "Test String", "str for testing",
                                    labels={"ls1", "ls2"})
        self.core.health.add_metric("test_gauge", HealthMetricType.gauge, "Test Gauge", "gauge for testing",
                                    labels={"lg1", "lg2"})

        # Metric set, gauge and str only
        self.core.health.metric_set("test_str", "test1", ls1="l1", ls2="l2")
        self.core.health.metric_set("test_gauge", -10, lg1="l1", lg2="l2")
        health = self.get_health()
        metrics = health["metrics"]
        counter = next((m for m in metrics if m["id"] == "test_counter"), None)
        self.assertIsNotNone(counter)
        self.assertEqual(counter["type"], "count")
        self.assertEqual(counter["description"], "counter for testing")
        self.assertEqual(counter["values"], {})
        string = next((m for m in metrics if m["id"] == "test_str"), None)
        self.assertIsNotNone(string)
        self.assertEqual(string["type"], "str")
        self.assertEqual(string["description"], "str for testing")
        self.assertEqual(string["values"], {'{"compute_id":"1","ls1":"l1","ls2":"l2"}': "test1"})
        gauge = next((m for m in metrics if m["id"] == "test_gauge"), None)
        self.assertIsNotNone(gauge)
        self.assertEqual(gauge["type"], "gauge")
        self.assertEqual(gauge["description"], "gauge for testing")
        self.assertEqual(gauge["values"], {'{"compute_id":"1","lg1":"l1","lg2":"l2"}': -10})

        # Metric inc, gauge and counter only
        self.core.health.metric_inc("test_counter", lc1="l1", lc2="l2")
        self.core.health.metric_inc("test_gauge", 5, lg1="l1", lg2="l2")
        health = self.get_health()
        metrics = health["metrics"]
        counter = next((m for m in metrics if m["id"] == "test_counter"), None)
        self.assertEqual(counter["values"], {'{"compute_id":"1","lc1":"l1","lc2":"l2"}': 1})
        gauge = next((m for m in metrics if m["id"] == "test_gauge"), None)
        self.assertEqual(gauge["values"], {'{"compute_id":"1","lg1":"l1","lg2":"l2"}': -5})
        string = next((m for m in metrics if m["id"] == "test_str"), None)
        self.assertEqual(string["values"], {'{"compute_id":"1","ls1":"l1","ls2":"l2"}': "test1"})

        # Metric dec, gauge only
        self.core.health.metric_dec("test_gauge", -10, lg1="l1", lg2="l2")
        health = self.get_health()
        metrics = health["metrics"]
        string = next((m for m in metrics if m["id"] == "test_str"), None)
        self.assertEqual(string["values"], {'{"compute_id":"1","ls1":"l1","ls2":"l2"}': "test1"})
        counter = next((m for m in metrics if m["id"] == "test_counter"), None)
        self.assertEqual(counter["values"], {'{"compute_id":"1","lc1":"l1","lc2":"l2"}': 1})
        gauge = next((m for m in metrics if m["id"] == "test_gauge"), None)
        self.assertEqual(gauge["values"], {'{"compute_id":"1","lg1":"l1","lg2":"l2"}': 5})

    def test_metric_different_package(self):
        self.core.health.add_metric("test", HealthMetricType.gauge, "Test Count", "counter for testing", package="asdf")
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test", 1, package="bsdf")
        self.assertIn("not found, the metric will not be set", str(ex.exception))

        self.core.health.metric_set("test", 1, package="asdf")

        health = self.get_health()
        metrics = health["metrics"]
        self.assertEqual("asdf", metrics[0]["package"])

    def test_metric_parent(self):
        with self.assertRaises(AssertionError) as ex:
            self.core.health.add_metric("test", HealthMetricType.gauge, "Test Count", "counter for testing",
                                        parent=True)
        self.assertIn("no parent is set", str(ex.exception))

        with override_context(PARENT="asdf"):
            self.core.health.add_metric("test", HealthMetricType.gauge, "Test Count", "counter for testing",
                                        parent=True)

            with self.assertRaises(ValueError) as ex:
                self.core.health.metric_set("test", 1)
            self.assertIn("not found, the metric will not be set", str(ex.exception))

            self.core.health.metric_set("test", 1, parent=True)

            health = self.get_health()
            metrics = health["metrics"]
            self.assertEqual("asdf", metrics[0]["package"])

    @override_settings(PARENT="asdf")
    def test_metric_parent_and_package(self):
        with self.assertRaises(AssertionError) as ex:
            self.core.health.add_metric("test", HealthMetricType.gauge, "Test Count", "counter for testing",
                                        parent=True, package="bsdf")
        self.assertIn("you can only set either parent or package", str(ex.exception))

    def test_metrics_invalid_calls(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing",
                                    labels={"lc1", "lc2"})
        self.core.health.add_metric("test_str", HealthMetricType.str, "Test String", "str for testing",
                                    labels={"ls1", "ls2"})
        self.core.health.add_metric("test_gauge", HealthMetricType.gauge, "Test Gauge", "gauge for testing",
                                    labels={"lg1", "lg2"})

        # Wrong string calls (inc, dec)
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_inc("test_str", ls1="l1", ls2="l2")
        self.assertIn("of type str cannot be increased", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_dec("test_str", ls1="l1", ls2="l2")
        self.assertIn("of type str cannot be increased", str(ex.exception))

        # Wrong counter calls (set, dec)
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_counter", 1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be set", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_inc("test_counter", -1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be decreased", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_dec("test_counter", 1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be decreased", str(ex.exception))

        # Wrong labels
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_gauge", 1, lc1="l1", lg2="l2")
        self.assertIn("labels do not match the metric definition", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_gauge", 1, lg2="l2")
        self.assertIn("labels do not match the metric definition", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_gauge", 1, lc2="l2")
        self.assertIn("labels do not match the metric definition", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_gauge", 1)
        self.assertIn("labels do not match the metric definition", str(ex.exception))

        # Wrong data type
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_gauge", "test", lg1="l1", lg2="l2")
        self.assertIn("of type gauge cannot be set to a non-numeric value", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_inc("test_gauge", "1", lg1="l1", lg2="l2")
        self.assertIn("of type gauge cannot be set to a non-numeric value", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_inc("test_counter", "1", lg1="l1", lg2="l2")
        self.assertIn("of type count cannot be set to a non-numeric value", str(ex.exception))
        with self.assertRaises(ValueError) as ex:
            self.core.health.metric_set("test_str", 123, lg1="l1", lg2="l2")
        self.assertIn("of type str cannot be set to a non-string value", str(ex.exception))

    @override_settings(TESTING=False)
    def test_metrics_invalid_calls_prod(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing",
                                    labels={"lc1", "lc2"})
        self.core.health.add_metric("test_str", HealthMetricType.str, "Test String", "str for testing",
                                    labels={"ls1", "ls2"})
        self.core.health.add_metric("test_gauge", HealthMetricType.gauge, "Test Gauge", "gauge for testing",
                                    labels={"lg1", "lg2"})

        # Wrong string calls (inc, dec)
        with self.assertLogs() as cm:
            self.core.health.metric_inc("test_str", ls1="l1", ls2="l2")
        self.assertIn("of type str cannot be increased", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_dec("test_str", ls1="l1", ls2="l2")
        self.assertIn("of type str cannot be increased", str(cm.output))

        # Wrong counter calls (set, dec)
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_counter", 1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be set", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_inc("test_counter", -1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be decreased", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_dec("test_counter", 1, lc1="l1", lc2="l2")
        self.assertIn("of type count cannot be decreased", str(cm.output))

        # Wrong labels
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_gauge", 1, lc1="l1", lg2="l2")
        self.assertIn("test_gauge labels do not match the metric definition", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_gauge", 1, lg2="l2")
        self.assertIn("test_gauge labels do not match the metric definition", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_gauge", 1, lc2="l2")
        self.assertIn("test_gauge labels do not match the metric definition", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_gauge", 1)
        self.assertIn("test_gauge labels do not match the metric definition", str(cm.output))

        # Wrong data type
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_gauge", "test", lg1="l1", lg2="l2")
        self.assertIn("of type gauge cannot be set to a non-numeric value", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_inc("test_gauge", "1", lg1="l1", lg2="l2")
        self.assertIn("of type gauge cannot be set to a non-numeric value", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_inc("test_counter", "1", lg1="l1", lg2="l2")
        self.assertIn("of type count cannot be set to a non-numeric value", str(cm.output))
        with self.assertLogs() as cm:
            self.core.health.metric_set("test_str", 123, lg1="l1", lg2="l2")
        self.assertIn("of type str cannot be set to a non-string value", str(cm.output))

    def test_compute_id_label(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing")
        self.core.health.metric_inc("test_counter")

        health = self.get_health()
        metrics = health["metrics"]
        self.assertEqual([], metrics[0]["labels"])
        self.assertEqual(1, metrics[0]["values"]['{"compute_id":"1"}'])

    def test_health_pong_metric_correct_types(self):
        self.core.health.add_metric("test_str", HealthMetricType.str, "Test String", "str for testing")
        self.core.health.add_metric("test_int", HealthMetricType.gauge, "Test Count", "int for testing")
        self.core.health.add_metric("test_float", HealthMetricType.gauge, "Test Count", "float for testing")
        self.core.health.metric_set("test_str", "123")
        self.core.health.metric_set("test_int", 123)
        self.core.health.metric_set("test_float", 123.123)
        health = HealthPongMessage.model_validate(self.get_health())
        self.assertEqual("123", health.metrics[0].values['{"compute_id":"1"}'])
        self.assertEqual(123, health.metrics[1].values['{"compute_id":"1"}'])
        self.assertEqual(123.123, health.metrics[2].values['{"compute_id":"1"}'])

    def test_metric_clear(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing",
                                    labels={"lc1", "lc2"})
        self.core.health.metric_inc("test_counter", lc1="l1", lc2="l2")
        self.core.health.metric_inc("test_counter", 3, lc1="l2", lc2="l3")
        self.core.health.metric_inc("test_counter", 1, lc1="keep1", lc2="keep1")
        self.core.health.metric_inc("test_counter", 1, lc1="keep2", lc2="keep2")
        metric = list(self.core.health.metrics.values())[0]
        self.assertEqual(len(metric.values), 4)
        self.core.health.metric_clear("test_counter", values_to_keep=[{"lc1": "keep1", "lc2": "keep1"},
                                                                      {"lc1": "keep2", "lc2": "keep2"}])
        self.assertEqual(len(metric.values), 2)
        self.assertIn('{"compute_id":"1","lc1":"keep2","lc2":"keep2"}', metric.values)
        self.assertIn('{"compute_id":"1","lc1":"keep2","lc2":"keep2"}', metric.values)
        self.core.health.metric_inc("test_counter", lc1="l1", lc2="l2")
        self.assertEqual(len(metric.values), 3)
        self.assertEqual(metric.values['{"compute_id":"1","lc1":"l1","lc2":"l2"}'], 1)
        self.core.health.metric_clear("test_counter")
        self.assertEqual(len(metric.values), 0)

    def test_delete_metric_value(self):
        self.core.health.add_metric("test_counter", HealthMetricType.count, "Test Count", "counter for testing",
                                    labels={"lc1", "lc2"})
        self.core.health.add_metric("test_gauge", HealthMetricType.gauge, "Test Gauge", "gauge for testing",
                                    labels={"lg1", "lg2"})
        self.core.health.add_metric("test_str", HealthMetricType.str, "Test String", "str for testing",
                                    labels={"ls1", "ls2"})

        metric_c = self.core.health.metrics[self.core.health._check_id("test_counter")]
        self.core.health.metric_inc("test_counter", 1, lc1="l1", lc2="l2")
        self.core.health.metric_inc("test_counter", 2, lc1="l2", lc2="l3")
        self.assertEqual(len(metric_c.values), 2)
        self.assertIn('{"compute_id":"1","lc1":"l1","lc2":"l2"}', metric_c.values)
        self.core.health.metric_set("test_counter", None, lc1="l1", lc2="l2")
        self.assertEqual(len(metric_c.values), 1)
        self.assertNotIn('{"compute_id":"1","lc1":"l1","lc2":"l2"}', metric_c.values)

        metric_c = self.core.health.metrics[self.core.health._check_id("test_gauge")]
        self.core.health.metric_inc("test_gauge", 1, lg1="l1", lg2="l2")
        self.core.health.metric_set("test_gauge", 2, lg1="l2", lg2="l3")
        self.assertEqual(len(metric_c.values), 2)
        self.assertIn('{"compute_id":"1","lg1":"l1","lg2":"l2"}', metric_c.values)
        self.core.health.metric_set("test_gauge", None, lg1="l1", lg2="l2")
        self.assertEqual(len(metric_c.values), 1)
        self.assertNotIn('{"compute_id":"1","lg1":"l1","lg2":"l2"}', metric_c.values)

        metric_c = self.core.health.metrics[self.core.health._check_id("test_str")]
        self.core.health.metric_set("test_str", "1", ls1="l1", ls2="l2")
        self.core.health.metric_set("test_str", "2", ls1="l2", ls2="l3")
        self.assertEqual(len(metric_c.values), 2)
        self.assertIn('{"compute_id":"1","ls1":"l1","ls2":"l2"}', metric_c.values)
        self.core.health.metric_set("test_str", None, ls1="l1", ls2="l2")
        self.assertEqual(len(metric_c.values), 1)
        self.assertNotIn('{"compute_id":"1","ls1":"l1","ls2":"l2"}', metric_c.values)
