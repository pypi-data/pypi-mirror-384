import contextlib
import functools
import inspect
import io
import json
import logging
import multiprocessing
import os
import random
import signal
import subprocess
import sys
import threading
import time
import unittest
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import cast
from unittest import TestCase, mock

import requests
import sentry_sdk.envelope
import sentry_sdk.utils
import urllib3
from sentry_sdk.consts import EndpointType
# noinspection PyProtectedMember
from sentry_sdk.tracing import _SpanRecorder

import openmodule
from openmodule import sentry
from openmodule.config import settings, override_settings
from openmodule.core import init_openmodule, shutdown_openmodule
from openmodule.dispatcher import MessageDispatcher
from openmodule.models.base import ZMQMessage, Gateway, Direction
from openmodule.models.io import IoMessage
from openmodule.rpc import RPCServer
from openmodule.sentry import init_sentry, deinit_sentry
from openmodule.utils.io import IoListener
from openmodule_test.sentry import SentryTestMixin
from openmodule_test.utils import wait_for_value
from openmodule_test.zeromq import ZMQTestMixin


class SentryInitTestCase(ZMQTestMixin):

    def tearDown(self):
        if openmodule.core._core_thread:
            shutdown_openmodule()
        super().tearDown()

    def test_init_during_debug_override(self):
        """
        sentry=True activates sentry, even in debug mode
        """

        # test b)
        config = self.zmq_config()
        config.DEBUG = True
        config.TESTING = False
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=True, dsn="http://test@test/1")
        self.assertNotIn("not activating sentry", str(cm.output))
        self.assertTrue(openmodule.core._core_thread.sentry_was_initialized)

    def test_init_during_testing(self):
        """
        sentry=True activates sentry, even in test mode
        """

        # test a)
        config = self.zmq_config()
        config.DEBUG = False
        config.TESTING = True
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=True, dsn="http://test@test/1")
        self.assertNotIn("not activating sentry", str(cm.output))
        self.assertTrue(openmodule.core._core_thread.sentry_was_initialized)

    def test_init_during_production(self):
        """
        sentry=None -> this is the default value, only activated if debug=False and testing=False
        """

        # test a)
        config = self.zmq_config()
        config.DEBUG = False
        config.TESTING = False
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=False, dsn="http://test@test/1")
        self.assertNotIn("not activating sentry", str(cm.output))  # explicitly setting false does not log this
        self.assertFalse(openmodule.core._core_thread.sentry_was_initialized)

    def test_init_during_debug(self):
        """
        sentry=None -> this is the default value
          a) don't init during testing
          b) and don't init during debug
          + logs that it was not initialized
        """

        # test b)
        config = self.zmq_config()
        config.DEBUG = True
        config.TESTING = False
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=None, dsn="http://test@test/1")
        self.assertIn("not activating sentry", str(cm.output))
        self.assertFalse(openmodule.core._core_thread.sentry_was_initialized)

    def test_init_during_testing_no_sentry(self):
        """
        sentry=None -> this is the default value
          a) don't init during testing
          b) and don't init during debug
          + logs that it was not initialized
        """

        # test a)
        config = self.zmq_config()
        config.DEBUG = False
        config.TESTING = True
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=None, dsn="http://test@test/1")
        self.assertIn("not activating sentry", str(cm.output))
        self.assertFalse(openmodule.core._core_thread.sentry_was_initialized)

    def test_init_during_production_no_sentry(self):
        """
        sentry=None -> this is the default value, only activated if debug=False and testing=False
        """

        # test a)
        config = self.zmq_config()
        config.DEBUG = False
        config.TESTING = False
        with self.assertLogs() as cm:
            init_openmodule(config, context=self.zmq_context(), sentry=None, dsn="http://test@test/1")
        self.assertNotIn("not activating sentry", str(cm.output))
        self.assertTrue(openmodule.core._core_thread.sentry_was_initialized)

    @override_settings(GATE="einfahrt")
    def test_init_with_gate(self):
        init_openmodule(self.zmq_config(), context=self.zmq_context(), sentry=True, dsn="http://test@test/1")
        self.assertEqual(sentry_sdk.get_global_scope()._extras["gate"], "einfahrt")

    def test_sentry_requires_dsn(self):
        config = self.zmq_config()
        config.DEBUG = False
        config.TESTING = False
        with self.assertRaises(ValueError) as e:
            init_openmodule(config, context=self.zmq_context(), sentry=None, dsn=None)
        self.assertEqual(str(e.exception), "sentry DSN is required")
        self.assertFalse(openmodule.core._core_thread.sentry_was_initialized)

    @override_settings(GATE="einfahrt")
    def test_sentry_init(self):
        config = self.zmq_config()
        init_openmodule(config, context=self.zmq_context(), sentry=True, dsn="http://test@test/1")
        self.assertTrue(openmodule.core._core_thread.sentry_was_initialized)
        scope = sentry_sdk.get_global_scope()
        self.assertIsInstance(scope.client, sentry_sdk.client.Client)
        self.assertIsInstance(scope.client.transport, sentry.StoringTransport)
        self.assertEqual(scope.client.options["release"], "test@test-version")
        self.assertEqual(scope.client.options["server_name"], "test-resource")
        self.assertEqual(scope.client.options["environment"], "staging")
        self.assertEqual(scope.client.options["dsn"], "http://test@test/1")
        self.assertEqual(scope.client.options["traces_sample_rate"], 0.0001)
        self.assertEqual(scope.client.options["profiles_sample_rate"], 0.001)
        self.assertEqual(scope._extras, {"name": "test", "gate": "einfahrt"})
        self.assertEqual(scope._contexts, {'device': {'model': 'test-resource', 'name': 'test-resource'}})
        self.assertEqual(sentry._topics_to_ignore, ["io"])
        self.assertEqual(sentry._functions_to_ignore, ["message_handler.openmodule.utils.io.IoListener._on_io_message"])

    @override_settings(NAME="test")
    def test_service_name_generation(self):
        settings.NAME = "om_service_test_1"
        kwargs = {}
        sentry._update_sentry_config(kwargs)
        self.assertEqual(kwargs["release"], "service-test@test-version")

        settings.NAME = "om_service_test"
        kwargs = {}
        sentry._update_sentry_config(kwargs)
        self.assertEqual(kwargs["release"], "service-test@test-version")

        settings.NAME = "service_test_1"
        kwargs = {}
        sentry._update_sentry_config(kwargs)
        self.assertEqual(kwargs["release"], "service-test@test-version")

        settings.NAME = "service_test"
        kwargs = {}
        sentry._update_sentry_config(kwargs)
        self.assertEqual(kwargs["release"], "service-test@test-version")

    def test_sentry_ignore_topics(self):
        self.assertEqual(sentry._topics_to_ignore, ["io"])
        init_openmodule(self.zmq_config(), context=self.zmq_context(), sentry=True, dsn="http://test@test/1",
                        topics_to_ignore=["test"])
        self.assertEqual(sentry._topics_to_ignore, ["test"])

    def test_sentry_ignore_functions(self):
        self.assertEqual(sentry._functions_to_ignore, ["message_handler.openmodule.utils.io.IoListener._on_io_message"])
        init_openmodule(self.zmq_config(), context=self.zmq_context(), sentry=True, dsn="http://test@test/1",
                        functions_to_ignore=["test"])
        self.assertEqual(sentry._functions_to_ignore, ["test"])


class SentryTestCase(SentryTestMixin):
    def setUp(self):
        super().setUp()
        init_sentry("http://test@test/1")
        sentry_sdk.get_client().options["traces_sample_rate"] = 1.0

    def tearDown(self):
        super().tearDown()
        deinit_sentry()

    @contextlib.contextmanager
    def isolated_transaction(self, *args, **kwargs):
        with sentry_sdk.isolation_scope():
            with sentry_sdk.start_transaction(*args, **kwargs) as transaction:
                yield transaction

    def assert_spans(self, span_recorder: _SpanRecorder, expected: list[str | None]):
        spans = [span.description for span in span_recorder.spans]
        self.assertEqual(spans, expected)

    def assert_tags(self, span_recorder: _SpanRecorder, expected: dict[str, str]):
        self.assertGreater(len(span_recorder.spans), 0)
        scope: sentry_sdk.Scope = span_recorder.spans[0].containing_transaction.scope
        self.assertEqual(scope._tags, expected)

    def test_sentry_init(self):
        sentry_sdk.capture_message("test message")
        envelopes = self.get_sent_envelopes()
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(len(envelopes[0].items), 1)
        self.assertEqual(envelopes[0].items[0].payload.json["message"], "test message")

    def test_sentry_logging_integration(self):
        logging.error("Some error, please help!")
        envelopes = self.get_sent_envelopes()
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(len(envelopes[0].items), 1)
        self.assertEqual(envelopes[0].items[0].payload.json["logger"], "root")
        self.assertEqual(envelopes[0].items[0].payload.json["level"], "error")
        self.assertEqual(envelopes[0].items[0].payload.json["logentry"],
                         {"message": "Some error, please help!", "params": []})

    def test_create_full_context_with_trace(self):
        with sentry.trace("test1"):
            with sentry.trace("test2"):
                sentry_sdk.set_tag("test", "test")
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder
        self.assert_spans(span_recorder, ["test2"])  # test1 is the transaction
        envelope = self.get_sent_envelopes()
        self.assertEqual(len(envelope), 1)
        self.assertEqual(envelope[0].items[0].payload.json["tags"], {"test": "test"})

    def test_use_existing_transaction_with_trace(self):
        with self.isolated_transaction(description="test3") as transaction:
            with sentry.trace("test4"):
                sentry_sdk.set_tag("test", "test")
                self.assertEqual(transaction, sentry_sdk.Scope.get_current_scope().transaction)
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder
        self.assert_spans(span_recorder, ["test4"])
        envelope = self.get_sent_envelopes()
        self.assertEqual(len(envelope), 1)
        self.assertEqual(envelope[0].items[0].payload.json["tags"], {"test": "test"})

    def test_trace_decorator_without_param(self):
        @sentry.trace
        def func():
            nonlocal span_recorder
            sentry_sdk.set_tag("test", "test")
            span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            func()
        # func.__module__ is needed to work with unittest and pytest (pycharm test and tox)
        self.assert_spans(span_recorder, [
            f"{func.__module__}.SentryTestCase.test_trace_decorator_without_param.<locals>.func"])
        envelope = self.get_sent_envelopes()
        self.assertEqual(len(envelope), 1)
        self.assertEqual(envelope[0].items[0].payload.json["tags"], {"test": "test"})

    def test_trace_decorator_with_param(self):
        @sentry.trace("other_func")
        def func():
            nonlocal span_recorder
            sentry_sdk.set_tag("test", "test")
            span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            func()
        self.assert_spans(span_recorder, ["other_func"])
        envelope = self.get_sent_envelopes()
        self.assertEqual(len(envelope), 1)
        self.assertEqual(envelope[0].items[0].payload.json["tags"], {"test": "test"})

    def test_trace_context_without_name(self):
        with sentry.trace("parent"):
            with sentry.trace():
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder
        self.assert_spans(span_recorder, [None])

    def test_trace_with_invalid_name_param(self):
        with self.assertRaises(ValueError) as e:
            # Is obviously not a string
            # noinspection PyTypeChecker
            with sentry.trace(55):
                self.fail("should not be reached")
        # PyCharm might say it is unreachable, but it is not
        # noinspection PyUnreachableCode
        self.assertEqual(str(e.exception), "Name should be a string or the function that is being decorated.")

    def test_trace_partial(self):
        def func():
            nonlocal span_recorder
            span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        other_func = sentry.trace(functools.partial(func))
        with sentry.trace("parent"):
            other_func()
        self.assert_spans(span_recorder, [
            f"partial(<function {func.__module__}.SentryTestCase.test_trace_partial.<locals>.func>)"])

    def test_trace_lambda(self):
        span_recorder: list[_SpanRecorder] = []
        func = lambda: span_recorder.append(sentry_sdk.Scope.get_current_scope().transaction._span_recorder)

        other_func = sentry.trace(func)
        inspect.signature(other_func)
        with sentry.trace("parent"):
            other_func()
        self.assert_spans(span_recorder[0], [
            f"{func.__module__}.SentryTestCase.test_trace_lambda.<locals>.<lambda>"])

    def test_trace_builtin(self):
        func = sentry.trace(dir)
        with self.assertRaises(ValueError):
            inspect.signature(func)
        func("test")

    def test_trace_class_method(self):
        class ExampleClass:
            @sentry.trace
            def method(self):
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass().method()
        self.assert_spans(span_recorder, [
            f"{ExampleClass.__module__}.SentryTestCase.test_trace_class_method.<locals>.ExampleClass.method"])

    def test_trace_class_class_method(self):
        class ExampleClass:
            @classmethod
            @sentry.trace
            def method(cls):
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass.method()
        self.assert_spans(span_recorder, [
            f"{ExampleClass.__module__}.SentryTestCase.test_trace_class_class_method.<locals>.ExampleClass.method"])

    def test_trace_class_static_method(self):
        class ExampleClass:
            @staticmethod
            @sentry.trace
            def method():
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass.method()
        self.assert_spans(span_recorder, [
            f"{ExampleClass.__module__}.SentryTestCase.test_trace_class_static_method.<locals>.ExampleClass.method"])

    def test_trace_class_method_with_name(self):
        class ExampleClass:
            @sentry.trace("func")
            def method(self):
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass().method()
        self.assert_spans(span_recorder, ["func"])

    def test_trace_class_class_method_with_name(self):
        class ExampleClass:
            @classmethod
            @sentry.trace("func")
            def method(cls):
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass.method()
        self.assert_spans(span_recorder, ["func"])

    def test_trace_class_static_method_with_name(self):
        class ExampleClass:
            @staticmethod
            @sentry.trace("func")
            def method():
                nonlocal span_recorder
                span_recorder = sentry_sdk.Scope.get_current_scope().transaction._span_recorder

        span_recorder: _SpanRecorder | None = None
        with sentry.trace("parent"):
            ExampleClass.method()
        self.assert_spans(span_recorder, ["func"])

    def test_io_message_not_traced(self):
        with sentry.continue_trace_zmq_message_receive("io", {}):
            pass
        with sentry.continue_trace_zmq_message_receive("not-io", {}):
            pass
        envelopes = self.get_sent_envelopes()
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(len(envelopes[0].items), 1)
        self.assertEqual(envelopes[0].items[0].payload.json["transaction"], "not-io/")

    def test_ignored_function(self):
        sentry._functions_to_ignore = ["test-ignore"]
        with sentry.trace("test-ignore"):
            pass
        with sentry.trace("not-test-ignore"):
            pass
        envelopes = self.get_sent_envelopes()
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(len(envelopes[0].items), 1)
        self.assertEqual(envelopes[0].items[0].payload.json["transaction"], "not-test-ignore")


class SentryInDispatcherTestCase(SentryTestMixin):
    def setUp(self):
        super().setUp()
        init_sentry("http://test@test/1")
        sentry_sdk.get_client().options["traces_sample_rate"] = 1.0
        self.dispatcher = None

    def tearDown(self):
        if self.dispatcher:
            self.dispatcher.shutdown()
        super().tearDown()
        deinit_sentry()

    def test_dispatcher(self):
        def handler(*_):
            pass

        self.dispatcher = MessageDispatcher()
        self.dispatcher.register_handler("test", ZMQMessage, handler, match_type=False)
        with sentry.trace("parent", sampled=True):
            self.dispatcher.dispatch("test", ZMQMessage(type="test").model_dump())

        envelopes = self.get_sent_envelopes()
        self.assertEqual(len(envelopes), 1)
        self.assertEqual(len(envelopes[0].items), 1)
        self.assertEqual(envelopes[0].items[0].payload.json["transaction"], "parent")
        self.assertEqual(len(envelopes[0].items[0].payload.json["spans"]), 2)
        span_names = [span["description"] for span in envelopes[0].items[0].payload.json["spans"]]
        handler_name = "message_handler.tests.test_sentry.SentryInDispatcherTestCase.test_dispatcher.<locals>.handler"
        self.assertEqual(span_names, ["test/test", handler_name])

    def test_io_handler_not_traced(self):
        self.dispatcher = MessageDispatcher()
        IoListener(self.dispatcher)
        self.dispatcher.dispatch("io", IoMessage(edge=1, gateway=Gateway(gate="test", direction=Direction.IN),
                                                 type="io", pin="1", value=1).model_dump())
        with self.assertRaises(TimeoutError):
            self.get_sent_envelopes()

    def test_io_topic_creates_scope(self):
        scope = sentry_sdk.get_isolation_scope()
        with sentry.continue_trace_zmq_message_receive(
                "io", {"sentry-trace": "e6b4de069f9a4e03b7012bb1eec1af08-a7d7309ad4ccc9ec-1"}):
            self.assertNotEqual(scope, sentry_sdk.get_isolation_scope())
        self.assertEqual(scope, sentry_sdk.get_isolation_scope())
        with self.assertRaises(TimeoutError):
            self.get_sent_envelopes()

    def test_multi_worker_dispatcher(self):
        def handler(*_):
            envelopes_got.wait(1)
            handled.set()

        handled = threading.Event()
        envelopes_got = threading.Event()
        self.dispatcher = MessageDispatcher(executor=ThreadPoolExecutor(max_workers=20))
        self.dispatcher.register_handler("test", ZMQMessage, handler, match_type=False)
        with sentry.trace("parent", sampled=True):
            self.dispatcher.dispatch("test", ZMQMessage(type="test").model_dump())
        first_envelopes = self.get_sent_envelopes()
        envelopes_got.set()
        self.assertTrue(handled.wait(timeout=1))
        second_envelopes = self.get_sent_envelopes(timeout=1)
        self.assertEqual(len(first_envelopes), 1)
        self.assertEqual(len(first_envelopes[0].items), 1)
        self.assertEqual(first_envelopes[0].items[0].payload.json["transaction"], "parent")
        self.assertEqual(len(first_envelopes[0].items[0].payload.json["spans"]), 0)

        self.assertEqual(len(second_envelopes), 1)
        self.assertEqual(len(second_envelopes[0].items), 1)
        self.assertEqual(second_envelopes[0].items[0].payload.json["transaction"], "test/test")
        self.assertEqual(len(second_envelopes[0].items[0].payload.json["spans"]), 1)
        handler_name = ("message_handler.tests.test_sentry.SentryInDispatcherTestCase."
                        "test_multi_worker_dispatcher.<locals>.handler")
        self.assertEqual(second_envelopes[0].items[0].payload.json["spans"][0]["description"], handler_name)


class SentryUtilsTestCase(SentryTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sentry.init_sentry("http://test@test/1")

    def test_zmq_message_fields(self):
        zmq_socket = mock.MagicMock()
        message = ZMQMessage(type="test")
        self.assertIsNone(message.sentry_trace)
        self.assertIsNone(message.baggage)
        with sentry.trace("test", sampled=True):
            message.publish_on_topic(zmq_socket, "test")
            traceparent = sentry.get_traceparent()
            baggage = sentry.get_baggage()
            self.assertEqual(message.sentry_trace, traceparent)
            self.assertEqual(message.baggage, baggage)
            self.assertIsNotNone(message.sentry_trace)
            self.assertIsNotNone(message.baggage)
        sent_message = json.loads(zmq_socket.send_multipart.call_args[0][0][1])
        self.assertEqual(sent_message["sentry-trace"], traceparent)
        self.assertEqual(sent_message["baggage"], baggage)

    def test_continue_from_zmq_message(self):
        zmq_socket = mock.MagicMock()
        with sentry.trace("test", sampled=True):
            msg = ZMQMessage(type="test_type")
            msg.publish_on_topic(zmq_socket, "topic_test")
            trace_id = sentry_sdk.get_current_span().trace_id
        msg_data = json.loads(msg.json_bytes())
        with sentry.continue_trace_zmq_message_process("topic_test", msg_data):
            self.assertEqual(sentry_sdk.get_current_span().description, "topic_test/test_type")
            self.assertTrue(sentry_sdk.get_current_span().sampled)
            self.assertEqual(sentry_sdk.get_current_span().trace_id, trace_id)

    def test_trace_id_changes(self):
        with sentry.trace("test1", sampled=True):
            trace_id = sentry_sdk.get_current_span().trace_id
        with sentry.trace("test2", sampled=True):
            self.assertNotEqual(sentry_sdk.get_current_span().trace_id, trace_id)

    def test_requests_raise_for_status_context(self):
        response = requests.Response()
        response.status_code = 400
        response.request = requests.Request()
        response.request.url = "http://the-test/400"
        response.raw = BytesIO(b"This is a test")
        response.headers = {"Content-Type": "text/plain"}
        with sentry.trace("test"):
            with self.assertRaises(requests.HTTPError) as e:
                response.raise_for_status()
            self.assertIn("This is a test", str(e.exception))
            self.assertEqual(sentry_sdk.get_isolation_scope()._contexts,
                             {"HTTP Response": {"content": "This is a test", "length": 14}})


class SentryTransportTestCase(TestCase):
    envelope_store = Path("/tmp/envelope_store")

    def setUp(self):
        self.envelope_store.unlink(missing_ok=True)
        sentry.init_sentry("http://test@test/1")
        self.transport.envelope_store = "/tmp/envelope_store"
        self.transport._compression_level = 0
        self.received_envelopes = []
        super().setUp()

    def tearDown(self):
        super().tearDown()
        sentry.deinit_sentry()
        self.envelope_store.unlink(missing_ok=True)

    @property
    def transport(self) -> sentry.StoringTransport:
        return cast(sentry.StoringTransport, sentry_sdk.get_global_scope().client.transport)

    def get_stored_envelopes(self) -> int:
        return self.transport.stored_envelopes

    def get_received_messages(self) -> int:
        return len(self.received_envelopes)

    @contextmanager
    def successful_send_request(self):
        def request_mock(_, __, body, ___):
            self.received_envelopes.append(sentry_sdk.envelope.Envelope.deserialize_from(io.BytesIO(body)))
            return urllib3.HTTPResponse(status=200)

        with mock.patch.object(self.transport, "_request", request_mock):
            yield

    def test_transport_store(self):
        sentry_sdk.capture_message("test message")
        self.assertEqual(wait_for_value(self.get_stored_envelopes, 1), 1)

    def test_store_append(self):
        sentry_sdk.capture_message("test message")
        sentry_sdk.capture_message("test message 2")
        wait_for_value(self.get_stored_envelopes, 2)
        self.assertEqual(len(self.envelope_store.read_bytes().splitlines()), 2)

    def test_parse_stored_envelope(self):
        def send_request_wrapper(body, headers, endpoint_type=EndpointType.ENVELOPE, envelope=None):
            nonlocal sent_envelope
            sent_envelope = envelope
            original_send_request(body, headers, endpoint_type, envelope)

        sent_envelope: sentry_sdk.envelope.Envelope | None = None
        original_send_request = self.transport._send_request
        self.transport._send_request = send_request_wrapper
        sentry_sdk.capture_message("test message")
        wait_for_value(self.get_stored_envelopes, 1)
        message, _ = self.transport.deserialize_request_data(self.envelope_store.read_bytes().splitlines()[0])
        parsed_envelope = sentry_sdk.envelope.Envelope.deserialize_from(io.BytesIO(message))
        del parsed_envelope.items[0].headers["length"]  # added during serialization
        self.assertEqual(repr(sent_envelope), repr(parsed_envelope))

    def test_send_stored_envelopes(self):
        self.transport.send_interval = 0.01
        sentry_sdk.capture_message("test message")
        wait_for_value(self.get_stored_envelopes, 1)
        with self.successful_send_request():
            sentry_sdk.capture_message("test message 2")
            wait_for_value(self.get_stored_envelopes, 0)
            wait_for_value(self.get_received_messages, 2)

    def test_send_stored_envelopes_slowly(self):
        self.transport.send_interval = 3
        sentry_sdk.capture_message("test message")
        sentry_sdk.capture_message("test message 2")
        wait_for_value(self.get_stored_envelopes, 2)
        with self.successful_send_request():
            sentry_sdk.capture_message("test message 3")
            with self.assertRaises(TimeoutError):
                wait_for_value(self.get_stored_envelopes, 0, timeout=1)
            wait_for_value(self.get_stored_envelopes, 1, timeout=3)
            with self.assertRaises(TimeoutError):
                wait_for_value(self.get_stored_envelopes, 0, timeout=1)
            wait_for_value(self.get_stored_envelopes, 0, timeout=3)
        wait_for_value(self.get_received_messages, 2)

    def test_envelope_store_drain(self):
        self.transport.max_stored_envelopes = 5
        self.transport.envelopes_drain = 3
        sentry_sdk.capture_message("test message 1")
        sentry_sdk.capture_message("test message 2")
        sentry_sdk.capture_message("test message 3")
        sentry_sdk.capture_message("test message 4")
        sentry_sdk.capture_message("test message 5")
        wait_for_value(self.get_stored_envelopes, 5)
        self.assertEqual(len(self.envelope_store.read_bytes().splitlines()), 5)
        sentry_sdk.capture_message("test message 6")
        wait_for_value(self.get_stored_envelopes, 3)
        self.assertEqual(len(self.envelope_store.read_bytes().splitlines()), 3)

    def test_do_not_store_traces(self):
        with sentry.trace("test", sampled=True):
            pass
        with self.assertRaises(TimeoutError):
            wait_for_value(self.get_stored_envelopes, 1, timeout=1)

    def test_get_stored_envelope_count_at_startup(self):
        self.envelope_store.write_bytes(b"{}\n{}\n{}\n")
        self.assertEqual(self.transport.stored_envelopes, 3)

    def test_survives_file_being_deleted(self):
        sentry_sdk.capture_message("test message")
        sentry_sdk.capture_message("test message 2")
        wait_for_value(self.get_stored_envelopes, 2)
        self.envelope_store.unlink()
        sentry_sdk.capture_message("test message")
        wait_for_value(self.get_stored_envelopes, 1)


class SentryFlushTestCase(TestCase):
    process: subprocess.Popen | None = None
    envelope_store = Path("/tmp/flush_test")
    env: dict

    def _kill_processes(self):
        # this is called in tear down and as a cleanup to make sure that under any circumstances the process is killed
        # otherwise you have processes lingering around, potentially blocking ports which is quite annoying
        if self.process and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGKILL)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = os.environ.copy()
        cls.env["PYTHONPATH"] = ":".join(sys.path)

    def setUp(self) -> None:
        self.envelope_store.unlink(missing_ok=True)
        self.addCleanup(self._kill_processes)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self._kill_processes()
        self.envelope_store.unlink(missing_ok=True)

    def test_no_flush_on_os_exit(self):
        self.process = subprocess.Popen(["python3", (Path(__file__).parent / "sentry_main.py").as_posix(), "os"],
                                        cwd=os.getcwd(), env=self.env)
        self.process.wait(timeout=5)
        self.assertEqual(self.process.poll(), 0)
        self.assertFalse(self.envelope_store.exists())

    def test_flush_on_sys_exit(self):
        self.process = subprocess.Popen(["python3", (Path(__file__).parent / "sentry_main.py").as_posix(), "sys"],
                                        cwd=os.getcwd(), env=self.env)
        self.process.wait(timeout=5)
        self.assertEqual(self.process.poll(), 0)
        self.assertTrue(self.envelope_store.exists())
        self.assertEqual(len(self.envelope_store.read_bytes().splitlines()), 1)

    def test_flush_on_clean_exit(self):
        self.process = subprocess.Popen(["python3", (Path(__file__).parent / "sentry_main.py").as_posix()],
                                        cwd=os.getcwd(), env=self.env)
        self.process.wait(timeout=5)
        self.assertEqual(self.process.poll(), 0)
        self.assertTrue(self.envelope_store.exists())
        self.assertEqual(len(self.envelope_store.read_bytes().splitlines()), 1)


@unittest.skipIf(True, "This test should not be part of the normal test suite. "
                       "Change True to False tu run. You also need to install psutil.")
class SentryTraceCpuUsageTestCase(TestCase):
    """
    This test case is used to compare the CPU usage of a function with and without sentry tracing.
    """
    execution_count = 10000
    sleep_time = 0.001
    processes: list[multiprocessing.Process] = []

    def _kill_processes(self):
        # this is called in tear down and as a cleanup to make sure that under any circumstances the process is killed
        # otherwise you have processes lingering around, potentially blocking ports which is quite annoying
        for process in self.processes:
            if process.is_alive():
                os.kill(process.pid, signal.SIGKILL)

    def setUp(self) -> None:
        self.addCleanup(self._kill_processes)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self._kill_processes()

    def test_compare(self):
        import psutil
        helper = SentryTraceHelper(self.execution_count, self.sleep_time)

        self.processes.append(multiprocessing.Process(target=helper.sentry_io))
        self.processes.append(multiprocessing.Process(target=helper.fake))
        for process in self.processes:
            process.start()
        sentry_percent = []
        no_sentry_percent = []
        ps = [psutil.Process(process.pid) for process in self.processes]
        while any(process.is_alive() for process in self.processes):
            if self.processes[0].is_alive():
                sentry_percent.append(ps[0].cpu_percent())
            if self.processes[1].is_alive():
                no_sentry_percent.append(ps[1].cpu_percent())
            time.sleep(0.0001)
        print()
        print(f"no sentry: {round(sum(no_sentry_percent) / len(no_sentry_percent), 2)}")
        print(f"sentry: {round(sum(sentry_percent) / len(sentry_percent), 2)}")
        ratio = (sum(sentry_percent) / len(sentry_percent)) / (sum(no_sentry_percent) / len(no_sentry_percent))
        print(f"increase: {round(ratio * 100 - 100, 2)}%")

    def test_profile(self):
        helper = SentryTraceHelper(self.execution_count, self.sleep_time)
        helper.sentry()


class SentryTraceHelper:
    def __init__(self, execution_count: int, sleep_time: float):
        self.execution_count = execution_count
        self.sleep_time = sleep_time

    @staticmethod
    def fake_handler(request, _):
        return request.model_dump()

    @contextlib.contextmanager
    def fake_trace(self, *_, **__):
        yield

    @staticmethod
    def simpler_get_client(_=None):
        return sentry_sdk.get_global_scope().client

    def fake(self):
        sentry.trace = self.fake_trace
        # noinspection PyProtectedMember
        sentry._Trace._trace_context = self.fake_trace
        sentry._continue_trace_zmq_message = self.fake_trace
        sentry_sdk.isolation_scope = self.fake_trace
        sentry_sdk.start_transaction = self.fake_trace
        self.sentry()

    @staticmethod
    def make_core(traces_sample_rate=0.001):
        settings.LOG_LEVEL = "WARNING"
        settings.TESTING = True
        settings.DEBUG = False
        sentry_sdk.utils.logger.setLevel(logging.WARNING)
        logging.basicConfig(level=logging.WARNING)
        return init_openmodule(settings, wait_for_broker=False, traces_sample_rate=traces_sample_rate,
                               sentry=True, dsn="http://test@test/1")

    def trace_all(self):
        self.sentry(traces_sample_rate=1.0)

    @staticmethod
    def _sentry_traceparent(traces_sample_rate=0.001):
        return f"e6b4de069f9a4e03b7012bb1eec1af08-a7d7309ad4ccc9ec-{int(random.random() < traces_sample_rate)}"

    def sentry_io(self, traces_sample_rate=0.001):
        core = None
        try:
            core = self.make_core(traces_sample_rate)
            IoListener(core.messages)
            for _ in range(self.execution_count):
                message = {"edge": 1, "gateway": {"gate": "test", "direction": "in"}, "type": "io", "pin": "1",
                           "value": 1, "sentry-trace": self._sentry_traceparent(traces_sample_rate)}
                with sentry.continue_trace_zmq_message_receive("io", message):
                    core.messages.dispatch("io", message)
                time.sleep(self.sleep_time)
        finally:
            if core:
                shutdown_openmodule()

    def sentry(self, traces_sample_rate=0.001):
        from openmodule.models.base import CostEntryData

        rpc_server = None
        core = None
        try:
            core = self.make_core(traces_sample_rate)
            sentry_sdk.get_client().transport.envelope_store = "/tmp/envelope_store"
            rpc_server = RPCServer(core.context)
            rpc_server.register_handler("test", "test", CostEntryData, CostEntryData, self.fake_handler)
            for _ in range(self.execution_count):
                # noinspection PyProtectedMember
                rpc_server._process_rpc_message("rpc-req-test", {
                    "sentry-trace": self._sentry_traceparent(traces_sample_rate),
                    "rpc_id": "ef9a5e77-bc95-404c-94de-9cf7b326c4d5", "resource": settings.RESOURCE, "type": "test",
                    "request": {"entry_type": "rate_change", "value": "test1", "group": "test", "account_id": "test"}})
                time.sleep(self.sleep_time)
        finally:
            if rpc_server:
                rpc_server.sub.close()
            if core:
                shutdown_openmodule()


if __name__ == "__main__":
    """
    This can be used to profile sentry performance with cProfile
    usage:
    python -m cProfile -o sentry.prof tests/test_sentry.py <sentry | fake | trace_all> <execution_count (optional)> <sleep_time (optional)>
    """
    _func = sys.argv[1]
    _execution_count = 1000
    _sleep_time = 0.01
    if len(sys.argv) > 2:
        _execution_count = int(sys.argv[2])
    if len(sys.argv) > 3:
        _sleep_time = float(sys.argv[3])
    SentryTraceHelper(_execution_count, _sleep_time).__getattribute__(_func)()
