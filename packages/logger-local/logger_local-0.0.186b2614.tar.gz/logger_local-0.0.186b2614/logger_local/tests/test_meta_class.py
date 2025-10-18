import logging
import re
import unittest
from abc import ABC
from datetime import datetime

from logger_local.src.meta_logger import MetaLogger, ABCMetaLogger, get_return_variables
# from .constants import logger_test_object
from .constants_tests_logger_local import LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT, LOGGER_STR
from python_sdk_remote.utilities import PRINT_STARS

# TODO: change to True, and fix the end test to return the correct function name instead of wrapper  # noqa E501
ASSERT_LOGGER_END = False

now = datetime.now()


class TestGetReturnVariables(unittest.TestCase):
    @staticmethod
    def multiline_docstring() -> str:
        """
        This is a multi-line docstring.
        It may contain return statements inside.
        :return: "inside docstring".
please keep this indentation
        """
        return "inside docstring"

    @staticmethod
    def if_1_return_1():
        if 1:
            return 1

    @staticmethod
    def return_with_variable():
        x = 1
        return x

    @staticmethod
    def return_with_expr_and_comment():
        # This function returns a value
        return 42  # The answer

    @staticmethod
    def return_with_string():
        return 'this is a return statement'

    @staticmethod
    def return_with_tuple_and_expression():
        x = 1
        return x, x + 1

    @staticmethod
    def return_with_invalid_identifier():
        return 1 + 2

    @staticmethod
    def return_inside_nested_functions():
        def inner():
            return "inner function"

        return inner()

    @staticmethod
    # TODO Since we stoped using lambda we can change the function name
    def return_with_lambda_and_variable():
        def y(x):
            return x + 1
        return y(5)

    @staticmethod
    def simple_return():
        a = 1
        return a

    @staticmethod
    def return_none():
        return None

    @staticmethod
    def return_tuple():
        a, b = 1, 2
        return a, b

    @staticmethod
    def return_with_expr():
        a = 1
        return a + 1

    @staticmethod
    def return_inside_if():
        a = 1
        if a > 0:
            return a
        return None

    @staticmethod
    def return_inside_for():
        for i in range(5):
            return i
        return None

    @staticmethod
    def return_inside_while():
        while True:
            return 42

    @staticmethod
    def return_inside_try():
        try:
            raise ValueError("error")
        except ValueError:
            return "caught"
        return None  # noqa

    @staticmethod
    def return_inside_nested_func():
        def inner():
            return "inner"

        return inner()

    @staticmethod
    # TODO Since we stoped using lambda we can change the function name
    def return_inside_lambda():
        def func(x):
            return x + 1
        return func(5)

    @staticmethod
    def return_in_string():
        return "return this string"

    @staticmethod
    def return_in_comment():
        # return this comment
        return "comment ignored"

    @staticmethod
    def multiple_returns():
        a, b = 1, 2
        return a, b
        return  # noqa

    @staticmethod
    def nested_tuple():
        a = 1
        b = 2
        return a, b, (a, b)

    def test_resturn_variable(self):
        test_cases = [
            (self.simple_return, ('a',)),
            (self.return_none, ('result',)),
            (self.return_tuple, ('a', 'b')),
            (self.return_with_expr, ("a + 1",)),  # with warning
            (self.return_inside_if, ('a',)),
            (self.return_inside_for, ('i',)),
            (self.return_inside_while, ('42',)),
            (self.return_inside_try, ("'caught'",)),
            (self.return_inside_nested_func, ('inner()',)),
            (self.return_inside_lambda, ('func(5)',)),
            (self.return_in_string, ("'return this string'",)),
            (self.return_in_comment, ("'comment ignored'",)),
            (self.multiple_returns, ('a', 'b')),
            (self.multiline_docstring, ("'inside docstring'",)),
            (self.if_1_return_1, ('1',)),
            (self.return_with_variable, ('x',)),
            (self.return_with_expr_and_comment, ('42',)),
            (self.return_with_string, ("'this is a return statement'",)),
            (self.return_with_tuple_and_expression, ('x', 'x + 1')),
            (self.return_with_invalid_identifier, ('1 + 2',)),
            (self.return_inside_nested_functions, ('inner()',)),
            (self.return_with_lambda_and_variable, ('y(5)',)),
            (self.nested_tuple, ('a', 'b', '(a, b)')),
        ]

        for func, expected in test_cases:
            try:
                result = get_return_variables(func)
            except Exception as e:
                print(f"Failed for {func.__name__}: {e}")
                raise e
            assert result == expected, f"Test failed for {func.__name__}: expected {expected}, got {result}"


class ExampleClass(metaclass=MetaLogger,
                   object=LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT,
                   level="debug",
                   ignore_cached_logger=True):
    def __init__(self, a, b):
        print("ExampleClass init")
        self.a = a
        self.b = b

    def __repr__(self):
        # this should be overridden by the metaclass, otherwise it can't access self.a in init logger.start
        return f"ExampleClass(a={self.a}, b={self.b})"

    def test1(self, c, *, d, e=1):
        a_plus_b = self.a + self.b
        return a_plus_b

    def test2(self):
        self.logger.info("Multiplying", object={"a": self.a, "b": self.b})
        a_mul_b = self.a * self.b
        return a_mul_b

    def test3(self, c=None):
        # test_var = "test_var"
        test3_result = self.a / self.b
        return test3_result

    @staticmethod
    def static_method(a, b):
        # x = "test static method"
        print(f"static method(a={a}, b={b})")
        static_method_result = ExampleClass.__private_method()
        return static_method_result

    @staticmethod
    def __private_method():
        var = "test private method"
        return var  # some comment

    @staticmethod
    def two_returns():
        if 0:
            return  # noqa
        elif 0:
            return None  # noqa
        return now

    @staticmethod
    def no_return():
        pass

    def return_multi_vars(self):
        """This function return multiple variables."""
        a, b = self.a, self.b; return a, b  # noqa

    def return_tuple(self):
        """This function return a tuple."""
        result_tuple = self.a, self.b
        return result_tuple

    @staticmethod
    def ambiguous_return(flag: bool) -> int | tuple[int, int]:
        a, b = 1, 2
        if flag:
            return a
        else:
            return a, b


class TestExampleClass(unittest.TestCase):

    def test_logger_exists(self):
        test_instance = ExampleClass(10, 0)
        self.assertIsNotNone(test_instance.logger)

    def test_test1(self):
        test_instance = ExampleClass(10, 0)
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            result = test_instance.test1(1, d=2)

        self.assertEqual(result, 10)

        start_regex = r".*START.*test1 \| kwargs={'self': ExampleClass\(a=10, b=0\), 'c': 1, 'd': 2}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*test1 \| kwargs={'a_plus_b': 10}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_test2(self):
        test_instance = ExampleClass(10, 0)
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            result = test_instance.test2()

        self.assertEqual(result, 0)

        start_regex = r".*START.*test2 \| kwargs={'self': ExampleClass\(a=10, b=0\)}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"

        info_regex = r".*INFO.*Multiplying \| kwargs={'a': 10, 'b': 0}"
        assert any(re.match(info_regex, line) for line in log_context.output)
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*test2 \| kwargs={'a_mul_b': 0}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa E501y

    def test_test3_exception(self):
        test_instance = ExampleClass(10, 0)
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            with self.assertRaises(ZeroDivisionError):
                test_instance.test3()
        if ASSERT_LOGGER_END:
            regex = (r".*ERROR.*test3 \| kwargs={'exception': ZeroDivisionError\('division by zero'\), "
                     r"'locals_before_exception': {'self': ExampleClass\(a=10, b=0\), 'c': None, 'test_var': 'test_var'}}")
            assert any(re.match(regex, line) for line in log_context.output), f"regex: {regex} not found in logs {log_context.output}"  # noqa E501

    def test_test_static_method(self):
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            ExampleClass.static_method(1, b=2)

        start_regex = r".*START.*static_method \| kwargs={'a': 1, 'b': 2}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"

        start_regex = r".*START.*__private_method \| kwargs={}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*static_method \| kwargs={'ExampleClass.__private_method\(\)': 'test private method'}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*__private_method \| kwargs={'var': 'test private method'}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_instance_test_static_method(self):
        test_instance = ExampleClass(10, 0)
        print(f"test_instance={test_instance}")
        # with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
        #     # TODO Shall we add a=
        #     test_instance.static_method(3, b=4)
        print(f"test_instance.static_method(3, b=4) __name__{__name__}")
        with self.assertLogs(logger="logger_local.src.logger_local", level=logging.DEBUG + 1) as log_context:
            # TODO Shall we add a=
            test_instance.static_method(3, b=4)

        start_regex = r".*START.*static_method \| kwargs={'a': 3, 'b': 4}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"

        start_regex = r".*START.*__private_method \| kwargs={}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*static_method \| kwargs={'ExampleClass.__private_method\(\)': 'test private method'}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*__private_method \| kwargs={'var': 'test private method'}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_test_2_returns(self):
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            ExampleClass.two_returns()

        start_regex = r".*START.*two_returns \| kwargs={}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*two_returns \| kwargs={'now': %s}" % re.escape(repr(now))
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_test_no_return(self):
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            ExampleClass.no_return()

        start_regex = r".*START.*no_return \| kwargs={}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*no_return \| kwargs={'result': None}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_return_multi_vars(self):
        test_instance = ExampleClass(10, 0)
        print(f"{PRINT_STARS}test_return_multi_vars __name__={__name__} LOGGER_STR={LOGGER_STR}")
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:  # noqa E501
            result = test_instance.return_multi_vars()

        self.assertEqual(result, (10, 0))

        start_regex = r".*START.*return_multi_vars \| kwargs={'self': ExampleClass\(a=10, b=0\)}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*return_multi_vars \| kwargs={'a': 10, 'b': 0}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_return_tuple(self):
        test_instance = ExampleClass(10, 0)
        with self.assertLogs(logger=LOGGER_STR, level=logging.DEBUG + 1) as log_context:
            result = test_instance.return_tuple()

        self.assertEqual(result, (10, 0))

        start_regex = r".*START.*return_tuple \| kwargs={'self': ExampleClass\(a=10, b=0\)}"
        assert any(re.match(start_regex, line) for line in
                   log_context.output), f"regex: {start_regex} not found in logs {log_context.output}"
        if ASSERT_LOGGER_END:
            end_regex = r".*END.*return_tuple \| kwargs={'result_tuple': \(10, 0\)}"
            assert any(re.match(end_regex, line) for line in log_context.output), f"regex: {end_regex} not found in logs {log_context.output}"  # noqa

    def test_ambiguous_return(self):
        # The logs are wrong, but the function should not raise
        ExampleClass.ambiguous_return(True)
        ExampleClass.ambiguous_return(False)


class AbstractClass(ABC, metaclass=ABCMetaLogger):
    pass


class ExampleSon(AbstractClass, ExampleClass):
    # This will raise without the ABCMetaLogger above
    pass


class AnotherSon(ExampleClass):  # This will send empty kwargs to MetaLogger
    pass


if __name__ == '__main__':
    unittest.main()
