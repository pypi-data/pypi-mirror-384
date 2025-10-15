import contextlib
import logging
import random
import string
import time
from contextlib import contextmanager
from typing import Generator

import orjson
import zmq

from openmodule import sentry
from openmodule.dispatcher import MessageDispatcher
from openmodule.models.base import ZMQMessage


def _internal_get_pub_socket(context, config, linger=100) -> zmq.Socket:
    socket: zmq.Socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.LINGER, linger)
    socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
    socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 3600)
    socket.connect(config.BROKER_SUB)
    return socket


def get_sub_socket(context, config, linger=0) -> zmq.Socket:
    socket: zmq.Socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.LINGER, linger)
    socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
    socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 3600)
    socket.connect(config.BROKER_PUB)
    return socket


def get_pub_socket(context, config, linger=100) -> zmq.Socket:
    raise AssertionError(
        "This function must not be used. Use core().publish instead (OM-697, OM-700). This is because the pub_socket "
        "receives all subscriptions which will result in a memory leak until a message is sent to the socket."
    )


def wait_for_connection(dispatcher: MessageDispatcher, pub_socket=None, pub_lock=None, timeout=100):
    """
    waits until the pub_socket's messages can be received at the dispatcher.
    This dispatcher needs to run in a separate thread as this method is blocking
    :param dispatcher: message dispatcher
    :param pub_socket: socket for message publishing (defaults to the core's pub socket, if None)
    :param pub_lock: optionally locks the lock during publishing
    :param timeout: timeout in sec
    """

    if pub_socket is None:
        from openmodule.core import core
        current_core = core()
        assert current_core, "either a core must be running or you have to pass a pub_socket"
        pub_socket = current_core.pub_socket
        pub_lock = current_core.pub_lock

    pub_lock = pub_lock or contextlib.nullcontext()
    received = False

    def handler(_):
        """ handler to set received true"""
        nonlocal received
        received = True

    # topic needs to start with __ping because these messages are ignored by the deeplog
    random_topic = "__ping_" + "".join(random.choices(string.ascii_letters, k=10))

    listener = dispatcher.register_handler(random_topic, ZMQMessage, handler, match_type=False)

    check_delay = 0.1
    check_iterations = int(timeout / check_delay) + 1

    message = ZMQMessage(type="connection-check")
    for x in range(check_iterations):
        with pub_lock:
            message.publish_on_topic(pub_socket, random_topic)

        time.sleep(check_delay)
        if received:
            break

    dispatcher.unregister_handler(listener)
    if not received:
        raise TimeoutError("could not connect to the message broker in time")


@contextmanager
def receive_message_from_socket(sub_socket: zmq.Socket) -> Generator[tuple[str | None, dict | None], None, None]:
    """
    :param sub_socket: zmq socket to receive
    Enters a sentry trace for the received message. For this reason, the function should be used as a context manager.
    :yields: a tuple containing (None, None) if an invalid message was received
             otherwise yields a tuple containing (topic: str, message: dict)
    """
    parts = sub_socket.recv_multipart()
    if len(parts) != 2:
        logging.error(f"received a zmq message with an invalid number of parts: {len(parts)}")
        yield None, None
        return

    topic, message = parts

    try:
        message_dict = orjson.loads(message)
    except orjson.JSONDecodeError as e:
        logging.error(f"received a zmq message with an invalid json. parsing error: {str(e)}")
        yield None, None
    else:
        if not isinstance(message_dict, dict):
            logging.error(f"received a zmq message which was not a dict but a {type(message)}")
            yield None, None
        else:
            decoded_topic = topic.decode("utf8")
            with sentry.continue_trace_zmq_message_receive(decoded_topic, message_dict):
                yield decoded_topic, message_dict
