import logging
import os
import shutil
import signal
import threading
import warnings
from concurrent.futures.thread import ThreadPoolExecutor

import zmq

from openmodule import sentry
from openmodule.alert import AlertHandler
from openmodule.config import validate_config_module
from openmodule.dispatcher import ZMQMessageDispatcher
from openmodule.health import HealthHandlerType, Healthz, HealthPingMessage
from openmodule.logging import init_logging
from openmodule.messaging import _internal_get_pub_socket, get_sub_socket, receive_message_from_socket, \
    wait_for_connection
from openmodule.models.base import ZMQMessage
from openmodule.sentry import init_sentry, should_activate_sentry, deinit_sentry
from openmodule.threading import get_thread_wrapper
from openmodule.connection_status import ConnectionStatusListener


class OpenModuleCore(threading.Thread):
    database = None

    def __init__(self, context, config, messages_executor=None):
        super().__init__(target=get_thread_wrapper(self._run))
        self.internal_thread = threading.Thread(target=get_thread_wrapper(self._run_internal))

        self.context = context
        self.config = config
        self.sentry_was_initialized = False

        self.pub_lock = threading.Lock()
        self.sub_lock = threading.Lock()

        self.pub_socket = _internal_get_pub_socket(self.context, self.config, linger=1000)
        self.sub_socket = get_sub_socket(self.context, self.config)
        self.sub_socket_internal = get_sub_socket(self.context, self.config)

        self.messages = ZMQMessageDispatcher(self.sub_socket, executor=messages_executor)
        self._messages_internal = ZMQMessageDispatcher(self.sub_socket_internal)

        from openmodule.rpc import RPCClient
        self.rpc_client = RPCClient(self._messages_internal, _warn=False)

        self.log = logging.getLogger(self.__class__.__name__)
        self.health = Healthz(self)
        self.alerts = AlertHandler(self)
        self.connection_listener = ConnectionStatusListener(self._messages_internal, self.rpc_client)
        self._messages_internal.register_handler("healthz", HealthPingMessage, self.health.process_message,
                                                 match_type=True)

    def init_database(self):
        from openmodule.database.database import Database
        if self.config.TESTING:
            self.database = Database(self.config.DATABASE_FOLDER, self.config.NAME, alembic_path="../src/database")
        else:
            self.database = Database(self.config.DATABASE_FOLDER, self.config.NAME)

    def start(self) -> None:
        super().start()
        self.internal_thread.start()

    def join(self, timeout: float | None = None) -> None:
        super().join(timeout)
        self.internal_thread.join(timeout)

    def _run(self):
        try:
            while True:
                with receive_message_from_socket(self.sub_socket) as (topic, message):
                    if topic is not None:
                        self.messages.dispatch(topic, message)
        except zmq.ContextTerminated:
            self.log.debug("context terminated, core shutting down")
        finally:
            with self.pub_lock:
                self.pub_socket.close()
            self.sub_socket.close()

    def _run_internal(self):
        try:
            while True:
                with receive_message_from_socket(self.sub_socket_internal) as (topic, message):
                    if topic is not None:
                        self._messages_internal.dispatch(topic, message)
                        self.connection_listener.check_timeout()
        except zmq.ContextTerminated:
            pass
        finally:
            self.sub_socket_internal.close()

    @sentry.trace(op="topic.send")
    def publish(self, message: ZMQMessage, topic: str):
        assert isinstance(topic, str), "topic must be a string"
        with self.pub_lock:
            message.publish_on_topic(self.pub_socket, topic)

    def shutdown(self):
        self._messages_internal.shutdown(wait=True)
        self.messages.shutdown(wait=True)
        if self.database:
            self.database.shutdown()
        self.context.term()


_core_thread: OpenModuleCore | None = None


def sigterm_handler(*_):
    raise KeyboardInterrupt()


def init_dsgvo_config():
    if os.path.exists("/data") and os.path.exists("/data/config.yml"):
        shutil.copyfile("/data/config.yml", "/data/tmp.yml")
        shutil.move("/data/tmp.yml", "/data/dsgvo-config.yml")
    if os.path.exists("/data") and os.path.exists("dsgvo-default.yml"):
        shutil.copyfile("dsgvo-default.yml", "/data/tmp.yml")
        shutil.move("/data/tmp.yml", "/data/dsgvo-default.yml")


def print_environment(core: OpenModuleCore):
    core.log.info(f"Service: {core.config.NAME} (version:{core.config.VERSION})")
    if core.config.DEBUG:
        core.log.warning(
            "\n"
            "        DEBUG MODE is active.\n"
            "        Deactivate by setting environment variable DEBUG=False.\n"
            "        Debug is disabled per default when a version string is set or ran inside docker.\n"
        )


def init_openmodule(config, *, dsn: str = None, sentry=None, logging=True, dsgvo=True,
                    health_handler: HealthHandlerType | None = None,
                    context=None, database=False, catch_sigterm=True,
                    dispatcher_max_threads=1, wait_for_broker=True, **sentry_kwargs) -> OpenModuleCore:
    if health_handler:
        warnings.warn(
            "health_handler is deprecated, and will simply be ignored. Please use metrics "
            "and alerts to send health information",
            DeprecationWarning
        )

    context = context or zmq.Context()
    validate_config_module(config)

    global _core_thread
    assert not _core_thread, "openmodule core already running"

    if dispatcher_max_threads > 1:
        executor = ThreadPoolExecutor(max_workers=dispatcher_max_threads)
    else:
        executor = None

    _core_thread = OpenModuleCore(context, config, messages_executor=executor)
    _core_thread.start()

    if logging:
        init_logging(_core_thread)
    print_environment(_core_thread)

    if wait_for_broker:
        _core_thread.log.info("connecting to the message broker")
        wait_for_connection(_core_thread.messages, _core_thread.pub_socket, _core_thread.pub_lock)
        wait_for_connection(_core_thread._messages_internal, _core_thread.pub_socket, _core_thread.pub_lock)
        _core_thread.log.info("connection established")

    # we activate sentry if
    # -> sentry=None (default) -> then we only activate in production
    # -> sentry=True/False this overrides and we activate/deactivate as desired
    if sentry is None:
        sentry = should_activate_sentry()
        if not sentry:
            _core_thread.log.info("not activating sentry in debug or test mode")

    if sentry:
        if dsn is None:
            raise ValueError("sentry DSN is required")
        init_sentry(dsn, **sentry_kwargs)
        _core_thread.sentry_was_initialized = True

    if dsgvo:
        init_dsgvo_config()

    if health_handler:
        _core_thread.health.health_handler = health_handler

    if database:
        _core_thread.init_database()

    if catch_sigterm and threading.current_thread().__class__.__name__ == "_MainThread":
        signal.signal(signal.SIGTERM, sigterm_handler)

    _core_thread.log.info("core startup complete")
    return _core_thread


def core() -> OpenModuleCore:
    return _core_thread


def shutdown_openmodule():
    global _core_thread
    assert _core_thread is not None, (
        "core thread is not running, did you call init_openmodule(...)?\n"
        "if its a testcase, maybe you forgot to call super().setUp()"
    )

    # we de-init sentry mostly to ensure consistency between testcases
    if _core_thread.sentry_was_initialized:
        deinit_sentry()

    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    current_core: OpenModuleCore = _core_thread
    _core_thread = None

    shutdown_done = threading.Event()

    def last_will():
        if not shutdown_done.wait(timeout=10):
            os._exit(99)

    if not (current_core.config.TESTING or current_core.config.DEBUG):
        last_will_thread = threading.Thread(target=last_will, daemon=True)
        last_will_thread.start()

    current_core.shutdown()
    current_core.join()
    shutdown_done.set()
