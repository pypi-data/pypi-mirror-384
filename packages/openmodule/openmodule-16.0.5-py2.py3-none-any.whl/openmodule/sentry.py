import base64
import functools
import inspect
import logging
import os.path
import time
from contextlib import contextmanager
from typing import Callable, overload, Generator, Any

import orjson
import requests
import sentry_sdk.integrations.logging
import sentry_sdk.tracing
import sentry_sdk.utils
import urllib3.exceptions
from sentry_sdk.consts import EndpointType
from sentry_sdk.envelope import Envelope

from openmodule.config import settings

_log = logging.getLogger("OmSentry")
_topics_to_ignore: list[str] = ["io"]
_functions_to_ignore: list[str] = ["message_handler.openmodule.utils.io.IoListener._on_io_message"]


@contextmanager
def noop_context():
    yield


def continue_trace_zmq_message_receive(topic: str, message: dict, **kwargs):
    """
    Continues a sentry trace for a received zmq message. (If already in a transaction, it will create a scope instead)
    Our ZMQMessage class contains the baggage and sentry-trace fields required for this, so the dict must contain these.
    :param topic: The topic of the message (as received from the ZMQ socket and decoded)
    :param message: The ZMQMessage as a dict (as received from the ZMQ socket and json loaded)
    """
    return _continue_trace_zmq_message(topic, message, "topic.receive", **kwargs)


def continue_trace_zmq_message_process(topic: str, message: dict, **kwargs):
    """
    Continues a sentry trace for a zmq message executor. (If already in a transaction, it will create a scope instead)
    Our ZMQMessage class contains the baggage and sentry-trace fields required for this, so the dict must contain these.
    :param topic: The topic of the message (as received from the ZMQ socket and decoded)
    :param message: The ZMQMessage as a dict (as received from the ZMQ socket and json loaded)
    """
    if topic in _topics_to_ignore:
        return noop_context()
    return _continue_trace_zmq_message(topic, message, "topic.process", **kwargs)


@overload  # pragma: no cover
def trace(
        name: None = None,
        op: sentry_sdk.consts.OP | str = sentry_sdk.consts.OP.FUNCTION,
        trace_headers: dict | None = None,
        force_new_transaction: bool = False,
        force_no_trace: bool = False,
        **span_kwargs) -> Callable[[Callable], Callable]:
    ...


@overload  # pragma: no cover
def trace(
        name: str,
        op: sentry_sdk.consts.OP | str = sentry_sdk.consts.OP.FUNCTION,
        trace_headers: dict | None = None,
        force_new_transaction: bool = False,
        force_no_trace: bool = False,
        **span_kwargs) -> Callable | Generator[sentry_sdk.tracing.Span, None, None]:
    ...


@overload  # pragma: no cover
def trace(
        name: Callable,
        op: sentry_sdk.consts.OP | str = sentry_sdk.consts.OP.FUNCTION,
        trace_headers: dict | None = None,
        force_new_transaction: bool = False,
        force_no_trace: bool = False,
        **span_kwargs) -> Callable:
    ...


def trace(
        name: str | Callable | None = None,
        op: sentry_sdk.consts.OP | str = sentry_sdk.consts.OP.FUNCTION,
        trace_headers: dict | None = None,
        force_new_transaction: bool = False,
        force_no_trace: bool = False,
        **span_kwargs):
    """
    Trace a function or a block of code.
    Can be used as a decorator or as a context manager.
    If used as a context manager, the func_or_name argument should be set.
    """
    span_kwargs["op"] = op
    span_kwargs["trace_headers"] = trace_headers
    span_kwargs["force_new_transaction"] = force_new_transaction
    span_kwargs["force_no_trace"] = force_no_trace
    if name is None:
        return _Trace(**span_kwargs)
    elif callable(name):
        return _Trace(**span_kwargs)(name)
    elif isinstance(name, str):
        return _Trace(name=name, **span_kwargs)
    else:
        raise ValueError("Name should be a string or the function that is being decorated.")


def get_baggage() -> str | None:
    """
    Only get the baggage if the current span is sampled, otherwise we don't really need it.
    """
    span = sentry_sdk.get_current_span()
    if span and span.sampled:
        return sentry_sdk.get_baggage()
    return None


get_traceparent = sentry_sdk.get_traceparent


def get_trace_headers(empty_if_not_sampled: bool = False) -> dict:
    if empty_if_not_sampled:
        span = sentry_sdk.get_current_span()
        if span and not span.sampled:
            return {}
    return {"sentry-trace": get_traceparent(), "baggage": get_baggage()}


class _Trace:
    """
    Context manager for sentry tracing.
    """
    span_kwargs: dict
    trace_headers: dict | None = None
    force_new_transaction: bool
    ctx: Any = None

    def __init__(self, *, trace_headers: dict | None = None, force_new_transaction: bool = False,
                 force_no_trace: bool = False, **span_kwargs):
        self.trace_headers = trace_headers
        self.force_new_transaction = force_new_transaction
        self.force_no_trace = force_no_trace
        self.span_kwargs = span_kwargs

    @contextmanager
    def _trace_context(self) -> Generator[None, None, None]:
        """
        If we are not in a span, start a new transaction. Should not be used directly.
        Otherwise, start a new span.
        If given a trace_headers dict, it will continue the trace with the given headers.
        """
        force_no_trace = self.force_no_trace or self.span_kwargs.get("name") in _functions_to_ignore

        def set_context():
            for key, value in extras.items():
                sentry_sdk.set_extra(key, value)
            sentry_sdk.set_tags(tags)
            for key, value in contexts.items():
                sentry_sdk.set_context(key, value)

        extras = self.span_kwargs.pop("extras", {})
        tags = self.span_kwargs.pop("tags", {})
        contexts = self.span_kwargs.pop("contexts", {})
        span = sentry_sdk.get_current_span()
        if span is None or self.force_new_transaction:
            with sentry_sdk.isolation_scope():
                if force_no_trace:
                    set_context()
                    yield
                else:
                    transaction: sentry_sdk.tracing.Transaction | None = None
                    if self.trace_headers and "sentry-trace" in self.trace_headers:
                        transaction = sentry_sdk.continue_trace(self.trace_headers, **self.span_kwargs)
                    with sentry_sdk.start_transaction(transaction=transaction, **self.span_kwargs) as transaction:
                        if transaction:
                            transaction.description = transaction.name
                        set_context()
                        yield
        elif not force_no_trace and span.sampled:
            self.span_kwargs.pop("source", None)
            with sentry_sdk.start_span(**self.span_kwargs):
                set_context()
                yield
        else:  # No need to start a span if the parent is not sampled
            set_context()
            yield

    def __enter__(self) -> None:
        self.ctx = self._trace_context()
        self.ctx.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.ctx.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to add tracing to functions.
        See also ``sentry_sdk.tracing.trace()``.
        """
        if "name" not in self.span_kwargs:
            self.span_kwargs["name"] = sentry_sdk.utils.qualname_from_function(func)
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def func_with_tracing(*args, **kwargs):
                with self._trace_context():
                    return await func(*args, **kwargs)
        else:
            @functools.wraps(func)
            def func_with_tracing(*args, **kwargs):
                with self._trace_context():
                    return func(*args, **kwargs)

        try:
            setattr(func_with_tracing, "__signature__", inspect.signature(func))
        except Exception:
            pass
        return func_with_tracing


def _continue_trace_zmq_message(topic: str, message: dict, op: str, **kwargs):
    name = f"{topic}/{message.get('type', '')}"
    return _Trace(trace_headers=message, op=op, name=name, source="zmq", origin="auto.zmq",
                  force_no_trace=topic in _topics_to_ignore, **kwargs)


class StoringTransport(sentry_sdk.transport.HttpTransport):
    """
    Custom transport that stores missed envelopes in a file and sends them later.
    If we ever use httpcore we need to inherit from sentry_sdk.transport.Http2Transport instead.
    Only stores the newest 100 envelopes.
    Sends the stored envelopes slowly to not overload the connection.
    """
    envelope_store = "/data/missed_sentry_events"
    _stored_envelopes: int | None = None
    is_offline = False
    successful_send = 0
    send_interval = 3
    max_stored_envelopes = 110
    envelopes_drain = 20

    @property
    def stored_envelopes(self):
        """
        Returns the number of stored envelopes. If called the first time, it will count the stored envelopes in the
            file. If the file does not exist, it will set the stored envelopes to 0.
        """
        if self._stored_envelopes is None:
            if os.path.exists(self.envelope_store):
                with open(self.envelope_store, "rb") as f:
                    self._stored_envelopes = sum(1 for _ in f)
            else:
                self._stored_envelopes = 0
        elif self._stored_envelopes:
            # In case the file was deleted somehow
            if not os.path.exists(self.envelope_store):
                self._stored_envelopes = 0
        return self._stored_envelopes

    @stored_envelopes.setter
    def stored_envelopes(self, value):
        self._stored_envelopes = value

    @staticmethod
    def serialize_request_data(body: bytes, headers: dict) -> bytes:
        """
        Serializes the body and headers into a single bytes object, that can be stored in a file in a single line.
        """
        return orjson.dumps({"body": base64.b64encode(body).decode(), "headers": headers})

    @staticmethod
    def deserialize_request_data(data: bytes) -> tuple[bytes, dict]:
        """
        Parses a stored envelope data into body and headers.
        """
        loaded_data = orjson.loads(data)
        return base64.b64decode(loaded_data["body"]), loaded_data["headers"]

    def store_envelope(self, body: bytes, headers: dict, envelope: Envelope | None = None):
        """
        Stores the envelope in a file. Only stores errors
        If the file is too large, it will remove the oldest envelopes.
        """
        try:
            if not any(item.data_category == "error" for item in envelope.items):
                return
            if self.stored_envelopes >= self.max_stored_envelopes:
                with open(self.envelope_store, "rb") as f:
                    lines = f.readlines()
                lines.append(self.serialize_request_data(body, headers))
                with open(self.envelope_store, "wb") as f:
                    f.writelines(lines[self.envelopes_drain:])
                self.stored_envelopes += 1 - self.envelopes_drain
            else:
                with open(self.envelope_store, "ab") as f:
                    f.write(self.serialize_request_data(body, headers) + b"\n")
                self.stored_envelopes += 1
        except Exception as e:
            _log.exception(e)

    def send_missed_envelope(self):
        """
        Sends the oldest stored envelope with a delay. This causes a slow drain of the stored envelopes.
        Can cause other envelopes to be delayed for a few seconds, but that is acceptable.
        """

        def capture_envelope_with_delay():
            while time.time() < submit_time:
                time.sleep(0.1)
            with sentry_sdk.utils.capture_internal_exceptions():
                self._send_request(*self.deserialize_request_data(envelope))

        submit_time = time.time() + self.send_interval
        if self.stored_envelopes and time.time() > (self.successful_send + self.send_interval):
            self.successful_send = time.time()
            with open(self.envelope_store, "rb") as f:
                envelopes = f.readlines()
            with open(self.envelope_store, "wb") as f:
                f.writelines(envelopes[1:])
            self.stored_envelopes -= 1
            envelope = envelopes[0]
            self._worker.submit(capture_envelope_with_delay)

    def _fetch_pending_client_report(self, force=False, interval=60):
        """
        Do not attach or send client reports if we are offline.
        Those will get lost anyway and might override actual stored envelopes.
        """
        if self.is_offline:
            return None
        return super()._fetch_pending_client_report(force, interval)

    def _send_request(self, body, headers, endpoint_type=EndpointType.ENVELOPE, envelope=None):
        """
        Stores the envelope if the request fails.
        Only captures urllib3 exceptions because anything else is a bug in the sentry-sdk.
        """
        try:
            super()._send_request(body, headers, endpoint_type, envelope)
        except urllib3.exceptions.HTTPError:
            self.is_offline = True
            self.store_envelope(body, headers, envelope)
            raise
        else:
            self.is_offline = False
            self.send_missed_envelope()


_patched_responses = set()


def _patch_requests_library():
    """
    Adds the response text to the sentry transaction if a raise_for_status is called on a failed request.
    This sets the context for the isolation_scope.
        This means that if multiple requests fail in a single transaction, only the last one will be stored.
    """
    if requests.Response in _patched_responses:
        return
    _patched_responses.add(requests.Response)

    original_raise_for_status = requests.Response.raise_for_status

    def new_raise_for_status(self: requests.Response):
        try:
            return original_raise_for_status(self)
        except requests.RequestException:
            sentry_sdk.set_context("HTTP Response", {
                "content": self.text[:1000], "length": len(self.text)})
            raise

    setattr(requests.Response, "raise_for_status", new_raise_for_status)


def _patch_sentry_method():
    def get_client(_=None):
        return client

    def is_gevent():  # pragma: no cover
        return gevent

    # Improve sentry sdk performance
    client = sentry_sdk.get_global_scope().client
    sentry_sdk.get_client = get_client
    sentry_sdk.scope.Scope.get_client = get_client
    gevent = sentry_sdk.utils.is_gevent()
    sentry_sdk.utils.is_gevent = is_gevent


def _update_sentry_config(kwargs: dict):
    # Set default values
    global _topics_to_ignore, _functions_to_ignore
    _topics_to_ignore = kwargs.pop("topics_to_ignore", ["io"])
    _functions_to_ignore = kwargs.pop(
        "functions_to_ignore", ["message_handler.openmodule.utils.io.IoListener._on_io_message"])

    if "traces_sampler" not in kwargs:
        kwargs.setdefault("traces_sample_rate", 0.0001)
    if "profiles_sampler" not in kwargs:
        kwargs.setdefault("profiles_sample_rate", 0.001)
    kwargs.setdefault("send_default_pii", True)
    kwargs.setdefault("shutdown_timeout", 2)
    kwargs["environment"] = "staging" if settings.DEV_DEVICE else "production"
    kwargs["server_name"] = settings.RESOURCE
    service_name = service_name_without_om = settings.NAME.lstrip("om_")
    if "_" in service_name_without_om:
        service_name, instance = service_name_without_om.rsplit("_", 1)
        if not instance.isdigit():
            service_name = service_name_without_om
    service_name = service_name.replace("_", "-")
    kwargs["release"] = f"{service_name}@{settings.VERSION}"
    kwargs.setdefault("transport", StoringTransport)

    # Update extras
    kwargs.setdefault("extras", {})
    kwargs["extras"]["name"] = settings.NAME
    if hasattr(settings, "GATE"):
        kwargs["extras"]["gate"] = settings.GATE
    kwargs.setdefault("contexts", {})
    kwargs["contexts"]["device"] = {"name": settings.RESOURCE, "model": settings.RESOURCE}


def init_sentry(dsn: str, **kwargs):
    """
    This function initializes Sentry with our predefined values.
    It also patches the requests library to add the response text to the sentry transaction.
    Does some additional setup to speed up the sentry sdk.
    Adds all extras (from kwargs or specific settings) to the sentry scope.

    :param dsn: Sentry DSN
    :param kwargs: Additional arguments for sentry_sdk.init
    """

    sentry_sdk.integrations.logging.ignore_logger(_log.name)

    _update_sentry_config(kwargs)
    extras = kwargs.pop("extras", {})
    contexts = kwargs.pop("contexts", {})
    tags = kwargs.pop("tags", {})
    sentry_sdk.init(dsn=dsn, **kwargs)

    _patch_requests_library()
    _patch_sentry_method()
    for key, value in extras.items():
        sentry_sdk.get_global_scope().set_extra(key, value)
    sentry_sdk.get_global_scope().set_tags(tags)
    for key, value in contexts.items():
        sentry_sdk.get_global_scope().set_context(key, value)


def deinit_sentry():
    sentry_sdk.get_global_scope().client.close()
    sentry_sdk.get_global_scope().set_client(None)


def should_activate_sentry() -> bool:
    """
    This function checks if for the given config Sentry should be activated or not.
    This is only false for debug mode. During testing we do not have a sentry-sender
    running anyway.

    :return: bool
    """
    return not (settings.DEBUG or settings.TESTING)
