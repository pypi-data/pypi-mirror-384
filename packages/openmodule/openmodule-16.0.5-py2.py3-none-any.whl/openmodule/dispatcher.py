import gzip
import json
import logging
import threading
import warnings
from collections import defaultdict
from concurrent.futures._base import Executor
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, DefaultDict, TypeVar, Generic

from pydantic_core import PydanticUndefined
import zmq
from pydantic import ValidationError, BaseModel
from sentry_sdk.utils import qualname_from_function

from openmodule import sentry
from openmodule.config import settings
from openmodule.models.base import ZMQMessage


class DummyExecutor(Executor):
    def __init__(self):
        self._shutdown = False
        self._shutdown_lock = threading.Lock()

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            fn(*args, **kwargs)

    def shutdown(self, wait=True):
        if wait:
            with self._shutdown_lock:
                self._shutdown = True
        else:
            self._shutdown = True


class Listener:
    def __init__(self, message_class: type[ZMQMessage], type: str | None, filter: Callable | None,
                 handler: Callable):
        self.filter = filter
        self.handler = sentry.trace(f"message_handler.{qualname_from_function(handler)}")(handler)
        self.type = type
        self.message_class = message_class

    def matches(self, message: dict):
        if self.type and message.get("type") != self.type:
            return False

        if self.filter:
            return self.filter(message)
        else:
            return True


EventArgs = TypeVar("EventArgs")


class EventListener(Generic[EventArgs], list):
    """
    note: the generic may not work as intended, but it is nevertheless a nice way to document the event
    handler arguments
    """
    log: logging.Logger | None = None

    def __init__(self, *args, log=None, raise_exceptions=False):
        super().__init__(args)
        self.raise_exceptions = raise_exceptions
        self.log = log or logging

    def __call__(self, *args: EventArgs):
        for f in self:
            try:
                f(*args)
            except zmq.ContextTerminated:
                raise
            except Exception as e:
                if self.raise_exceptions:
                    raise
                else:
                    self.log.exception(e)


ZMQMessageSub = TypeVar('ZMQMessageSub', bound=ZMQMessage)


class MessageDispatcher:
    def __init__(self, name=None, *, raise_validation_errors=False, raise_handler_errors=False,
                 executor: Executor | None = None):
        """
        :param name: optionally name the dispatcher for logging purposes
        :param raise_validation_errors: if true and received messages do not match a validation error is raised,
                                        this is useful in restricive code or testcases
        :param raise_handler_errors: if true and a message handler raises an exception, the exception is raised,
                                     this is useful in restricive code or testcases
        """

        assert executor is None or not (raise_handler_errors or raise_validation_errors), (
            "raise errors is only supported if no executor is used."
        )

        self.name = name
        self.log = logging.getLogger(f"{self.__class__.__name__}({self.name})")
        self.listeners: DefaultDict[str, list[Listener]] = defaultdict(list)
        self.raise_validation_errors = raise_validation_errors
        self.raise_handler_errors = raise_handler_errors
        self.executor = executor or DummyExecutor()
        self._new_transactions = not isinstance(self.executor, DummyExecutor)
        self._shutdown = False
        self._shutdown_lock = threading.Lock()

    @property
    def is_multi_threaded(self):
        if isinstance(self.executor, DummyExecutor):
            return False

        if isinstance(self.executor, (ThreadPoolExecutor, ProcessPoolExecutor)):
            # noinspection PyProtectedMember
            if self.executor._max_workers > 1:
                return True
            else:
                return False

        # unknown executor? assume multithreaded
        return True

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self.executor.shutdown(wait=wait)

    def unregister_handler(self, listener: Listener):
        for topic, listeners in self.listeners.items():
            try:
                listeners.remove(listener)
            except ValueError:
                pass

    def register_handler(self, topic: str,
                         message_class: type[ZMQMessageSub],
                         handler: Callable[[ZMQMessageSub], None], *,
                         filter: dict | Callable[[dict], bool] | None = None,
                         match_type=True):
        """
        registers a message handler. without any filters all messages from the topic are
        sent to the message handler.
        :param filter: a dictionary of values which must match in order for the message to
                       be further processed
        :param match_type: if set to true the message_class's type field is used as a filter.
                           equivalent to setting filter={"type": message_class.fields["type"].default}
        """

        assert isinstance(topic, str), "topic must be a string"

        if match_type:
            if valid_type := "type" in message_class.model_fields:
                valid_type &= message_class.model_fields["type"].default is not PydanticUndefined
            assert valid_type, (
                "\n\nYour message class definition does not set a `type` field, or the type field "
                "does not have a default value! To receive all message type pass `match_type=False` to "
                "`register_handler`. Otherwise please define a `type` for your message class."
            )
            type_ = message_class.model_fields["type"].default
        else:
            type_ = None

        listener = Listener(message_class, type_, filter, handler)
        self.listeners[topic].append(listener)

        if settings.TESTING and hasattr(handler, "__global__") and "/tests/" not in handler.__globals__['__file__']:
            # only doc string necessary for functions or lambdas (so not for mocks) outside of tests folder
            assert handler.__doc__, f"You need to describe the message handler {handler} with a doc string"

        return listener

    def dispatch(self, topic: str, message: dict | BaseModel):
        with self._shutdown_lock:
            if self._shutdown:
                # We need to drop messages after shutdown somewhere.
                # Cannot be done in the executor because it's a python builtin base class.
                # Could also be done in core, but it's better here because messages and _messages_internal are
                # both dispatched here.
                return
            assert isinstance(topic, str), "topic must be a string"

            if isinstance(message, BaseModel):
                message = message.model_dump()

            listeners = self.listeners.get(topic, [])
            for listener in listeners:
                if listener.matches(message):
                    message.update(sentry.get_trace_headers())
                    self.executor.submit(self.execute, topic, listener, message)

    def execute(self, topic: str, listener: Listener, message: dict):
        with sentry.continue_trace_zmq_message_process(
                topic, message, force_new_transaction=self._new_transactions):
            try:
                parsed_message = listener.message_class.model_validate(message)
            except ValidationError as e:
                if self.raise_validation_errors:
                    raise e from None
                else:
                    self.log.exception("Invalid message received")
            else:
                try:
                    listener.handler(parsed_message)
                except zmq.ContextTerminated:
                    raise
                except Exception as e:
                    if self.raise_handler_errors:
                        raise e from None
                    else:
                        self.log.exception("Error in message handler")


class SubscribingMessageDispatcher(MessageDispatcher):
    def __init__(self, subscribe: Callable[[str], None], name=None, *, raise_validation_errors=False,
                 raise_handler_errors=False, unsubscribe: Callable[[str], None] | None = None,
                 executor: Executor | None = None):
        super().__init__(name=name, raise_validation_errors=raise_validation_errors,
                         raise_handler_errors=raise_handler_errors, executor=executor)
        self.subscribe = subscribe
        self.unsubscribe = unsubscribe

    def register_handler(self, topic: str,
                         message_class: type[ZMQMessageSub],
                         handler: Callable[[ZMQMessageSub], None], *,
                         filter: dict | None = None,
                         match_type=True):
        assert isinstance(topic, str), "channel must be a string"

        self.subscribe(topic)
        return super().register_handler(topic, message_class, handler, filter=filter, match_type=match_type)

    def unregister_handler(self, listener: Listener):
        super().unregister_handler(listener)

        warn_no_unsubscribe = False
        for topic, listeners in self.listeners.items():
            if not listeners:
                if self.unsubscribe:
                    self.unsubscribe(topic)
                else:
                    warn_no_unsubscribe = True
                    break

        if warn_no_unsubscribe:
            warnings.warn("All handlers were unregistered from a topic, but no unsubscribe method was configured. "
                          "This may cause a performance overhead if too many unused subscriptions are kept. "
                          "Consider passing a unsubscribe method.", UserWarning, stacklevel=2)


class ZMQMessageDispatcher(SubscribingMessageDispatcher):
    def __init__(self, sub_socket: zmq.Socket, name=None, *, raise_validation_errors=False, raise_handler_errors=False,
                 executor: Executor | None = None):
        super().__init__(
            subscribe=lambda x: sub_socket.subscribe(x.encode("utf8")),
            unsubscribe=lambda x: sub_socket.unsubscribe(x.encode("utf8")),
            name=name,
            raise_validation_errors=raise_validation_errors,
            raise_handler_errors=raise_handler_errors,
            executor=executor
        )


class DeeplogMessageDispatcher(MessageDispatcher):
    def __init__(self, path: Path | str, name=None, *, raise_validation_errors=False, raise_handler_errors=False,
                 executor: Executor | None = None):
        super().__init__(name, raise_validation_errors=raise_validation_errors,
                         raise_handler_errors=raise_handler_errors, executor=executor)
        if not isinstance(path, Path):
            path = Path(path)

        assert path.is_dir()
        self.path = path
        self.current_timestamp = None

    def dispatch_hour(self, date_string):
        logging.info(f"Dispatching {date_string}")
        # prefer .gz files over .log since gz are finished
        gz_path = self.path / f"hour_{date_string}.log.gz"
        raw_path = self.path / f"hour_{date_string}.log"
        file_handle = None

        try:
            if gz_path.exists():
                file_handle = gzip.open(gz_path, "rb")

            elif raw_path.exists():
                file_handle = open(raw_path, "rb")

            else:
                raise FileNotFoundError(f"log file for hour {date_string} does not exist")

            try:
                for line in file_handle.readlines():
                    try:
                        topic, message = json.loads(line)
                    except Exception:
                        logging.warning("broken message skipped")
                    else:
                        self.current_timestamp = message.get("timestamp")
                        self.dispatch(topic, message)
            except EOFError as e:
                logging.error(str(e))

        finally:
            if file_handle:
                file_handle.close()

    def dispatch_all(self):
        hours = []
        for file in self.path.iterdir():
            if file.is_file() and file.name.startswith("hour_"):
                date_string = file.name[5:].split(".")[0]
                hours.append(date_string)

        hours.sort()
        for hour in hours:
            self.dispatch_hour(hour)
