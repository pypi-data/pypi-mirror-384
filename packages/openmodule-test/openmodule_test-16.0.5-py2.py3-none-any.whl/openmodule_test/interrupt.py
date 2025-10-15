import logging
import os
import queue
import sys
import time
import traceback
from multiprocessing import Process, Event
from signal import SIGINT, SIGKILL
from textwrap import dedent
from typing import Callable
from unittest import TestCase

import multiprocessing_logging

from openmodule.core import shutdown_openmodule
from openmodule_test.health import HealthTestMixin


class ExceptionProcess(Process):
    def __init__(self, *args, **kwargs):
        is_finished = Event()
        super().__init__(*args, **kwargs)
        self.is_finished = is_finished

    def run(self):
        try:
            super().run()
            self.is_finished.set()
        except Exception as e:
            logging.exception(e)


class MyMultiProcessingHandler(multiprocessing_logging.MultiProcessingHandler):
    def _receive(self):
        while True:
            try:
                if self._is_closed and self.queue.empty():
                    break

                record = self.queue.get(timeout=0.2)
                self.sub_handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except (BrokenPipeError, EOFError):
                break
            except queue.Empty:
                pass  # This periodically checks if the logger is closed.
            except:
                traceback.print_exc(file=sys.stderr)
                break

        self.queue.close()
        self.queue.join_thread()


def install_mp_handler(logger=None) -> bool:
    """Wraps the handlers in the given Logger with an MultiProcessingHandler.

    :param logger: whose handlers to wrap. By default, the root logger.
    """
    installed_handler = False

    if logger is None:
        logger = logging.getLogger()

    for i, orig_handler in enumerate(list(logger.handlers)):
        handler = MyMultiProcessingHandler("mp-handler-{0}".format(i), sub_handler=orig_handler)

        logger.removeHandler(orig_handler)
        logger.addHandler(handler)
        installed_handler = True

    return installed_handler


class InterruptTestMixin(TestCase):
    """
    Helper class for testing interrupts and exceptions in code
    for usage, look at file tests/test_interrupt
    """

    process: ExceptionProcess | None = None

    def _kill_process(self):
        # this is called in tear down and as a cleanup to make sure that under any circumstances the process is killed
        # otherwise you have processes lingering around, potentially blocking ports which is quite annoying
        if self.process and self.process.is_alive():
            os.kill(self.process.pid, SIGKILL)

    def setUp(self) -> None:
        self.installed_mp_handler = False
        self.addCleanup(self._kill_process)
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self._kill_process()

    def wait_for_setup(self):
        pass

    def _wait_for_and_uninstall_mp_handler(self, logger=None):
        """
        waits until the multiprocessing logging handler has finished
        """
        if logger is None:
            logger = logging.getLogger()

        closed = False
        for handler in logger.handlers:
            if isinstance(handler, multiprocessing_logging.MultiProcessingHandler):
                handler.close()
                closed = True

        assert self.installed_mp_handler == closed, ("No multiprocessing logging handler found to close.\n"
                                                     "\t\t\t\tDid you call `self.assertCleanShutdown()` outside "
                                                     "of the `self.assertLogs()` context manager?\n"
                                                     "\t\t\t\tCalling `self.assertCleanShutdown()` outside "
                                                     "of the context manager leads to OS errors.")

        multiprocessing_logging.uninstall_mp_handler(logger)

    def start_process(self, f: Callable):
        """
        starts the process and waits until it is responsive by calling calls wait_for_setup()
        """
        # we need this variable, because without the context manager `self.assertLogs()` the root logger,
        # has no handlers installed, so we cannot install the multiprocessing handler
        self.installed_mp_handler = install_mp_handler()
        self.process = ExceptionProcess(target=f)
        self.process.start()
        return self.process

    def assertCleanShutdown(self, process, shutdown_timeout: float = 3.0):
        """
        asserts that the process shuts down cleanly
        """
        if process.is_finished.wait(timeout=shutdown_timeout):
            self._wait_for_and_uninstall_mp_handler()
            return
        else:
            if process.is_alive():
                os.kill(process.pid, SIGKILL)
                raise TimeoutError("Process took to long for shutdown")
            else:
                raise AssertionError("Process did not finish gracefully")

    def send_signal_to_process(self, process: ExceptionProcess, signal: type[KeyboardInterrupt] | int):
        self.assertFalse(process.is_finished.is_set(), msg="process crashed before we could send the signal")
        if signal == KeyboardInterrupt:
            signal = SIGINT
        os.kill(process.pid, signal)

    def signal_in_function(self, f: Callable, signal: type[KeyboardInterrupt] | int, *,
                           raise_exception_after: float = 3.0, shutdown_timeout: float = 3.0):
        """
        wraps the helper functions into a single function because apparently everybody likes
        to write framework functions which are hard to adopt and do one single thing and nothing
        else. mostly here for backwards compatibility and reference how to use the testcase

        now deprecated because i can't stand it anymore
        :return: list of output lines
        """

        sys.stderr.write(dedent("""\
        \n\nsignal_in_function is deprecated. Please use the following pattern instead:

        ```
        try:
            with self.assertLogs() as cm:
                process = self.start_process(main_wrapper)
                self.wait_for_health()
                self.send_signal_to_process(process, SIGINT)
                self.assertCleanShutdown(process, shutdown_timeout=3)
        except Exception as e:
            for line in cm.output:
                print(line)
            raise e
        ```

        """))

        with self.assertLogs() as cm:
            try:
                process = self.start_process(f)
                self.wait_for_setup()
                time.sleep(raise_exception_after)
                self.send_signal_to_process(process, signal)
                self.assertCleanShutdown(process, shutdown_timeout=shutdown_timeout)
            except Exception as e:
                for line in cm.output:
                    print(line)
                raise e
        return cm.output


class MainTestMixin(HealthTestMixin, InterruptTestMixin):
    topics = ["healthpong"]
    protocol = "tcp://"

    def wait_for_setup(self):
        sys.stderr.write("\n\nPlease use wait_for_health instead")
        self.wait_for_health()

    def tearDown(self):
        try:
            shutdown_openmodule()
        except AssertionError:
            pass
        super().tearDown()
