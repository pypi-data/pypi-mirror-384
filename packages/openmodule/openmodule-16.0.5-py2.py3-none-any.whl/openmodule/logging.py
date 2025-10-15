import logging
import sys

import requests

_patched_exceptions = set()


def _patch_requests_library():
    """Adds the response text to the string representation of a requests.RequestException"""
    if requests.RequestException in _patched_exceptions:
        return
    _patched_exceptions.add(requests.RequestException)

    original_exception_string = requests.RequestException.__str__

    def new_exception_string(self: requests.RequestException):
        ret_str = original_exception_string(self)
        if self.response is not None:
            ret_str = f"{ret_str}: {self.response.text[:1000]}"
        return ret_str

    setattr(requests.RequestException, "__str__", new_exception_string)


def init_logging(core):
    assert hasattr(core.config, "LOG_LEVEL"), (
        "LOG_LEVEL setting not found in your config. In order to use logging please add \n"
        "> LOG_LEVEL = config.log_level()\n"
        "to your config.py"
    )
    _patch_requests_library()
    logging.basicConfig(level=core.config.LOG_LEVEL, stream=sys.stdout)
    logging.captureWarnings(True)
