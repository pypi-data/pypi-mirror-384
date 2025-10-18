import logging
import re
import unittest

from logger_local.src.meta_logger import Logger, module_wrapper
from .constants_tests_logger_local import LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT, LOGGER_STR

# TODO: change to True, and fix the end test to return the correct function name instead of wrapper
ASSERT_LOGGER_END = False


def foo() -> None:
    1 / 0  # noqa


def bar():
    one = 1
    return one


logger = Logger.create_logger(object=LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT, level="debug", ignore_cached_logger=True)
module_wrapper(logger)


class TestModuleWrapper(unittest.TestCase):
    def test_foo(self):
        with self.assertLogs(logger=LOGGER_STR, level="ERROR") as log_context:
            try:
                foo()
            except ZeroDivisionError:
                pass  # we expect this exception
        self.assertEqual(len(log_context.output), 1)

    def test_bar(self):
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG) as log_context:
            bar()

        start_regex = r".*START.*bar \| kwargs={}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"

        if ASSERT_LOGGER_END:
            end_regex = r".*END.*bar \| kwargs={'1': 1}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa: E501
