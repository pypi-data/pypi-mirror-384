import json
import os

import logger_local.src.debug_mode as debug_mode
from logger_local.src.logger_local import Logger
from logger_local.src.logger_output_enum import LoggerOutputEnum
# from logger_local.src.message_severity
from python_sdk_remote.constants_src_mini_logger_and_logger import LogMessageSeverity
from logger_local.src.meta_logger import log_function_decorator
from .constants_tests_logger_local import LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT

logger = Logger.create_logger(object=LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT,
                              ignore_cached_logger=True)

# Disable environment variables
debug_mode.DEFAULT_LOGGER_CONFIGURATION_JSON_PATH = None
debug_mode.DEFAULT_LOGGER_MINIMUM_SEVERITY = None
debug_mode.LOGGER_IS_WRITE_TO_SQL_ENV = None

current_directory = os.path.dirname(__file__)

DOT_LOGGER_JSON_EXAMPLE1 = '.logger.example1.json'
file_path = os.path.join(current_directory, DOT_LOGGER_JSON_EXAMPLE1)
with open(file_path, 'r') as file:
    EXAMPLE_DATA_1 = json.load(file)

# TODO Convert to json5
DOT_LOGGER_JSON_EXAMPLE2 = '.logger.example2.json'
file_path = os.path.join(current_directory, DOT_LOGGER_JSON_EXAMPLE2)
with open(file_path, 'r') as file:
    # TODO Add support to json5
    EXAMPLE_DATA_2 = json.load(file)


def add_debug_file(data):
    ADD_DEBUG_FILE_FUNCTION_NAME = 'add_debug_file()'
    logger.start(ADD_DEBUG_FILE_FUNCTION_NAME)

    with open(os.path.join(os.getcwd(), debug_mode.DEFAULT_LOGGER_JSON_SUFFIX), 'w') as f:
        json.dump(data, f)

    logger.end(ADD_DEBUG_FILE_FUNCTION_NAME)


@log_function_decorator(logger)
def remove_debug_file():
    os.remove(os.path.join(os.getcwd(), debug_mode.DEFAULT_LOGGER_JSON_SUFFIX))


def test_is_logger_output_debug_info_1():
    TEST_IS_LOGGER_OUTPUT_DEBUG_INFO_1_FUNCTION_NAME = 'test_is_logger_output_debug_info_1()'
    logger.start(TEST_IS_LOGGER_OUTPUT_DEBUG_INFO_1_FUNCTION_NAME)

    add_debug_file(EXAMPLE_DATA_1)

    try:
        debug_mode_instance = debug_mode.DebugMode(logger_minimum_severity=500)
    finally:
        remove_debug_file()

    result = debug_mode_instance.is_logger_output(
        component_id=1,
        logger_output=LoggerOutputEnum.Console,
        severity_level=501)
    logger.end(TEST_IS_LOGGER_OUTPUT_DEBUG_INFO_1_FUNCTION_NAME,
               object={'result': result})

    assert result


def test_is_logger_output_debug_mode_2():
    test_is_logger_output_debug_mode_2_function_name = \
        'test_IS_LOGGER_OUTPUT_DebugMode_2()'
    logger.start(test_is_logger_output_debug_mode_2_function_name)

    add_debug_file(EXAMPLE_DATA_2)

    try:
        debug_mode_instance = debug_mode.DebugMode(logger_minimum_severity=400)
    finally:
        remove_debug_file()

    # TODO Replace all Magic Numbers with constants
    result1 = debug_mode_instance.is_logger_output(
        # TODO Use constant instead of Magic Number
        component_id=2,
        logger_output=LoggerOutputEnum.Logzio,
        severity_level=502)
    print(f"result1: {result1}")
    result2 = debug_mode_instance.is_logger_output(
        component_id=2,
        logger_output=LoggerOutputEnum.MySQLDatabase,
        severity_level=503)
    print(f"result2: {result2}")
    result3 = debug_mode_instance.is_logger_output(
        component_id=2,
        logger_output=LoggerOutputEnum.Console,
        severity_level=499)
    print(f"result3: {result3}")

    logger.end(test_is_logger_output_debug_mode_2_function_name,
               object={'result1': result1,
                       'result2': result2,
                       'result3': result3})
    assert result1
    if not logger.get_is_write_to_sql():
        assert not result2
    else:
        assert result2
    # TODO Is it correct?
    assert result3


# TODO Please document and make sure this test is needed
def test_minimum_severity():
    TEST_MINIMUM_SEVERITY_FUNCTION_NAME = 'test_minimum_severity()'
    logger.start(TEST_MINIMUM_SEVERITY_FUNCTION_NAME)

    add_debug_file(EXAMPLE_DATA_2)

    TEST_COMPONENT_ID = 2
    logzio_severity = EXAMPLE_DATA_2[str(TEST_COMPONENT_ID)][LoggerOutputEnum.Logzio.value]

    try:
        debug_mode_instance = debug_mode.DebugMode(
            logger_minimum_severity=logzio_severity - 1)
    finally:
        remove_debug_file()

    # TODO was originally "test_minimum_severity_result1 = not debug_mode_instance..." Work in GHA. Locally works without the "not". Why?  # noqa: E501
    test_minimum_severity_result1 = not debug_mode_instance.is_logger_output(
        component_id=TEST_COMPONENT_ID,
        logger_output=LoggerOutputEnum.Logzio,
        severity_level=logzio_severity - 1)
    # TODO Shall we uncomment
    # assert test_minimum_severity_result1

    test_minimum_severity_result2 = debug_mode_instance.is_logger_output(
        component_id=TEST_COMPONENT_ID,
        logger_output=LoggerOutputEnum.Logzio,
        severity_level=logzio_severity)
    # TODO Shall we uncomment
    # assert test_minimum_severity_result2

    logger.info(TEST_MINIMUM_SEVERITY_FUNCTION_NAME, object={
        'test_minimum_severity_result1': test_minimum_severity_result1,
        'test_minimum_severity_result2': test_minimum_severity_result2})


def test_is_debug_everything():
    TEST_DEBUG_EVERYTHING_FUNCTION_NAME = 'test_is_debug_everything()'
    logger.start(TEST_DEBUG_EVERYTHING_FUNCTION_NAME)
    assert not os.path.exists(os.path.join(os.getcwd(),
                                           debug_mode.DEFAULT_LOGGER_JSON_SUFFIX))

    debug_mode_instance = debug_mode.DebugMode(logger_minimum_severity=500)

    result1 = debug_mode_instance.is_logger_output(
        component_id=2,
        logger_output=LoggerOutputEnum.Logzio,
        severity_level=501)
    result2 = debug_mode_instance.is_logger_output(
        component_id=2,
        logger_output=LoggerOutputEnum.Logzio,
        severity_level=502)

    logger.end(TEST_DEBUG_EVERYTHING_FUNCTION_NAME, object={
        'result1': result1,
        'result2': result2})
    assert result1
    assert result2


def test_invalid_logger_minimum_severity():
    INVALID_SEVERITY = 'invalid'

    try:
        result = False
        debug_mode.DebugMode(logger_minimum_severity=INVALID_SEVERITY)
    except Exception:
        result = True
    assert result


def test_int_minimum_severity():
    debug_mode_instance = debug_mode.DebugMode(logger_minimum_severity=15)
    assert debug_mode_instance.logger_minimum_severity == 15


def test_alpha_numeric_minimum_severity():
    debug_mode_instance = debug_mode.DebugMode(logger_minimum_severity='13')
    assert debug_mode_instance.logger_minimum_severity == 13


def test_enum_minimum_severity():
    debug_mode_instance = debug_mode.DebugMode(
        logger_minimum_severity='Information')
    assert debug_mode_instance.logger_minimum_severity == LogMessageSeverity.INFORMATION.value
