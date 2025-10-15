import logging
import time
from signal import SIGINT, SIGTERM
from unittest import TestCase

from openmodule.config import settings
from openmodule.core import init_openmodule, shutdown_openmodule
from openmodule_test.interrupt import InterruptTestMixin, MainTestMixin


def main_example():
    try:
        main_example.run = True
        t0 = time.time()
        while main_example.run and time.time() - t0 < 10:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.error("Keyboard")
    except Exception as e:
        logging.info(f"exception: {e}")
    else:
        logging.info("not running")
    finally:
        logging.info("killed")

    # we have to sleep some so the logs make their way to the parent process
    time.sleep(1)


class InterruptTest(InterruptTestMixin, TestCase):
    def test_keyboard(self):
        output = self.signal_in_function(main_example, KeyboardInterrupt)
        self.assertIn("Keyboard", str(output))

    def test_sigterm(self):
        with self.assertRaises(AssertionError) as e:
            self.signal_in_function(main_example, SIGTERM)
        self.assertIn("Process did not finish gracefully", str(e.exception))


def sleepy():
    try:
        t0 = time.time()
        while time.time() - t0 < 10:
            time.sleep(1)
    except:
        try:
            sleepy()
        except SystemExit:
            pass


class InterruptTimeoutTest(InterruptTestMixin, TestCase):
    function = staticmethod(sleepy)

    def test_exception(self):
        with self.assertRaises(TimeoutError) as e:
            self.signal_in_function(sleepy, KeyboardInterrupt)
        self.assertIn("Process took to long for shutdown", str(e.exception))


def main():
    core = init_openmodule(settings)
    main.run = True
    try:
        while main.run:
            time.sleep(1)
        logging.info("stopped")
    except KeyboardInterrupt:
        logging.error("keyboard")
    except Exception as e:
        print(e)
    finally:
        shutdown_openmodule()


def main_without_sighandler():
    core = init_openmodule(settings, catch_sigterm=False)
    main.run = True
    try:
        while main.run:
            time.sleep(1)
        logging.info("stopped")
    except KeyboardInterrupt:
        logging.error("keyboard")
    except Exception as e:
        print(e)
    finally:
        shutdown_openmodule()


class MainTest(MainTestMixin):
    def test_keyboard(self):
        output = self.signal_in_function(main, SIGINT)
        self.assertIn("keyboard", str(output))

    def test_docker_shutdown(self):
        output = self.signal_in_function(main, SIGTERM)
        self.assertIn("keyboard", str(output))

    def test_docker_uncaught_shutdown(self):
        with self.assertRaises(AssertionError) as e:
            self.signal_in_function(main_without_sighandler, SIGTERM)
        self.assertIn("Process did not finish gracefully", str(e.exception))


def exception_raiser():
    init_openmodule(settings, catch_sigterm=False)
    main.run = True
    try:
        while main.run:
            time.sleep(1)
            break_dict = dict()
            _ = break_dict["breaking"]
        logging.info("stopped")
    except KeyboardInterrupt:
        logging.error("keyboard")
    finally:
        shutdown_openmodule()


class ExceptionInFunctionTest(MainTestMixin):
    def test_uncaught_exception_in_function(self):
        with self.assertRaises(AssertionError) as e:
            self.signal_in_function(exception_raiser, KeyboardInterrupt)
        self.assertIn("Process did not finish gracefully", str(e.exception))
