import io
import logging
from unittest import TestCase, mock

import requests

import openmodule.logging


class LoggingTestCase(TestCase):
    def test_logging_to_stdout(self):
        logging.basicConfig(force=True)  # reset logging
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch("sys.stdout.write", stdout.write), mock.patch("sys.stderr.write", stderr.write):
            logging.warning("test")
        self.assertNotIn("test", stdout.getvalue())
        self.assertIn("test", stderr.getvalue())

        core = mock.MagicMock()
        core.config.LOG_LEVEL = logging.INFO
        for h in logging.root.handlers[:]:  # reset logging again
            logging.root.removeHandler(h)
            h.close()
        openmodule.logging.init_logging(core)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch("sys.stdout.write", stdout.write), mock.patch("sys.stderr.write", stderr.write):
            logging.warning("test")
        self.assertIn("test", stdout.getvalue())
        self.assertNotIn("test", stderr.getvalue())

    def test_requests_exception_log(self):
        openmodule.logging._patch_requests_library()
        response = requests.Response()
        response.status_code = 400
        response.request = requests.Request()
        response.request.url = "http://the-test/400"
        response.raw = io.BytesIO(b"This is a test")
        response.headers = {"Content-Type": "text/plain"}
        with self.assertRaises(requests.HTTPError) as e:
            response.raise_for_status()
        self.assertIn("This is a test", str(e.exception))
