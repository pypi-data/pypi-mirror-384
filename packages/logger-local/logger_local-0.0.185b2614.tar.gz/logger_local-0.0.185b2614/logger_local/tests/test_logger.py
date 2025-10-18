import json
import os
import re
import time
import traceback
from datetime import datetime
from typing import Any

import pytest
from python_sdk_remote.utilities import get_environment_name, PRINT_STARS
from url_remote.environment_name_enum import EnvironmentName

# TODO Can we delete the get_connection
from logger_local.src.connector_logger import ConnectorLogger, get_connection
# from logger_local.src.LoggerComponentEnum import LoggerComponentEnum
from logger_local.src.logger_component_enum import LoggerComponentEnum
from logger_local.src.logger_local import Logger, obfuscate_log_dict, MYSQL
# from logger_local.src.message_severity import LogMessageSeverity
from python_sdk_remote.constants_src_mini_logger_and_logger import LogMessageSeverity, StartEndEnum
# TODO Delete
# from logger_local.src.constants_src_logger_local import LOGGER_LOCAL_PYTHON_CODE_COMPONENT_ID
from .constants_tests_logger_local import (LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT,
                                           LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID,
                                           LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME,
                                           LOGGER_LOCAL_PYTHON_TEST_COMPONENT_CATEGORY,
                                           LOGGER_LOCAL_PYTHON_TEST_DEVELOPER_EMAIL_ADDRESS,
                                           )
# TODO Shall we use DebugMode or delete the bellow line?
# from ..src.debug_mode import DebugMode

# TODO: test LOGGER_CONFIGURATION_JSON_PATH

# TODO we prefer not to use Magic Numbers get_test_component_id(1)
TEST_COMPONENT_ID_1 = 5000002
TEST_COMPONENT_ID_2 = 5000003

DEBUG_MINIMUM_SEVERITY_TEST = "debug"


@pytest.fixture(scope="module")
def logger():
    logger = Logger.create_logger(object=LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT,
                                  level=DEBUG_MINIMUM_SEVERITY_TEST,
                                  ignore_cached_logger=True)
    logger.set_is_write_to_sql(True)
    # TODO We should delete the bellow line
    logger.set_is_write_to_sql(False)
    yield logger
    logger.set_is_write_to_sql(False)


# TODO Can we replace it with ConnectorLogger.get_test_connection()? and delete get_test_connection() here.
def get_test_connection():
    time.sleep(3)
    connection = get_connection(schema_name="logger")
    print("get_test_connection connection.is_connected()=", connection.is_connected())
    # Since we got in _mysql_connector.MySQLInterfaceError: Commands out of sync; you can't run this command now
    # TODO Do we need it?
    if connection.is_connected():
        connection.commit()
    return connection


GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX = 0
GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX = 1


def get_log(column: str,
            payload_object: dict,
            select_clause: str = "severity_id,message") -> tuple | None:
    connection = get_test_connection()
    if not connection:
        print("connection is None")
        return None
    # if !(connection.is_connected()):
    #     print("connection.is_connected()=False")
    #     return None
    else:
        print("connection==", connection)

    # Trying to resolve "mysql.connector.errors.OperationalError: MySQL Connection not available." error
    connection.reconnect()

    cursor = connection.cursor()
    sql_query = f"""SELECT {select_clause} FROM logger.logger_view
                    WHERE {column} = %s ORDER BY timestamp DESC LIMIT 1;"""
    cursor.execute(sql_query, (payload_object[column],))
    result = cursor.fetchone()
    cursor.close()
    return result


# TODO Add test of scenario where LOGGER_MINIMUM_SEVERITY was not defined
def test_log_with_only_logger_object(logger):
    object_to_insert_1 = {
        'payload': 'log from python -object_1 check',
        'password': 'very secret password'
    }
    logger.info(object=object_to_insert_1)
    GET_LOG_RECORD_COLUMN_IDX = 1
    result = get_log('payload', object_to_insert_1, select_clause="severity_id,record")
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.INFORMATION.value
    password = json.loads(result[GET_LOG_RECORD_COLUMN_IDX])['password']
    if get_environment_name() == EnvironmentName.PLAY1.value:
        assert password == 'very secret password'
    else:
        assert password == '***'


def test_error_with_only_logger_object(logger):
    object_to_insert_2 = {
        'payload': 'payload from error python -object_2',
    }
    logger.error(object=object_to_insert_2)
    result = get_log('payload', object_to_insert_2)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.ERROR.value


def test_verbose_with_only_logger_object(logger):
    object_to_insert_3 = {
        'client_ip_v4': 'ipv4-py',
        'client_ip_v6': 'ipv6-py',
        'latitude': 32,
        'longitude': 35,
        'variable_id': 5000001,
        'variable_value_old': 'variable_value_old-python-object_3',
        'variable_value_new': 'variable_value_new-python',
    }
    logger.verbose(object=object_to_insert_3)
    result = get_log('variable_value_old', object_to_insert_3)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.VERBOSE.value


def test_warn_with_only_logger_object(logger):
    object_to_insert_4 = {
        'client_ip_v4': 'ipv4-py',
        'client_ip_v6': 'ipv6-py',
        'latitude': 32,
        'longitude': 35,
        'activity': 'test from python',
        'activity_id': 5000001,
        'payload': 'payload from python -object_4',
        'variable_value_new': 'variable_value_new-python',
        'created_user_id': 5000001,
        'updated_user_id': 5000001
    }
    logger.warning(object=object_to_insert_4)
    result = get_log('payload', object_to_insert_4)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.WARNING.value


def test_add_message(logger):
    # option to insert only message
    message = 'only message error from python'
    logger.error(message)
    result = get_log('message', {'message': message})
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.ERROR.value


def test_debug_with_only_logger_object(logger):
    object_to_insert5 = {
        'payload': "Test python!!! check for debug insert"
    }
    logger.debug(object=object_to_insert5)
    result = get_log('payload', object_to_insert5)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.DEBUG.value


def test_start_with_only_logger_object(logger):
    object_to_insert6 = {
        'payload': "Test python!!! check for start insert"
    }
    logger.start(object=object_to_insert6)
    result = get_log('payload', object_to_insert6)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == StartEndEnum.START.value


def test_end_with_only_logger_object(logger):
    object_to_insert7 = {
        'payload': "Test python!!! check for end insert",
    }
    logger.end(object=object_to_insert7)
    result = get_log('payload', object_to_insert7)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == StartEndEnum.END.value


def test_init_with_only_logger_object(logger):
    message = "Test python!!! check for init insert"
    logger.init(message)
    result = get_log('message', {'message': message})
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.INIT.value


def test_exception_with_payload(logger):
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(True)
    stack_trace = ""
    message = "Test python!!! check for exception insert"
    try:
        print(f"{PRINT_STARS}test_exception_with_payload() before 5 / 0")
        5 / 0
    except Exception as exception:
        error_logger_ids_dict = logger.error(object={"exception": exception, "message": message})
        print(f"{PRINT_STARS}test_exception_with_payload() error_logger_ids_dict={error_logger_ids_dict}")
        stack_trace = str(traceback.format_exception(
            type(exception), exception, exception.__traceback__))

    connection = get_test_connection()
    cursor = connection.cursor()

    escaped_stack_trace = re.escape(stack_trace)
    pattern = f"%{escaped_stack_trace}%"
    print(f"test_exception_with_payload() pattern={pattern}")
    GET_LOGGER_SEVERITY_ID_AND_MESSAGE_BY_LOGGER_ID_SEVERITY_ID_COLUMN_IDX = 1
    GET_LOGGER_SEVERITY_ID_AND_MESSAGE_BY_LOGGER_ID_MESSAGE_IDX = 2
    if error_logger_ids_dict is None:
        # OLD
        print(f"{PRINT_STARS}test_exception_with_payload() error_logger_ids_dict is None. TODO Fix this")
        get_logger_severity_id_and_message_by_error_stack_sql_query = \
            ("SELECT logger_id, severity_id, message "
             "FROM logger.logger_view "
             "WHERE error_stack LIKE %s "
             "ORDER BY timestamp DESC LIMIT 1;")
        cursor.execute(get_logger_severity_id_and_message_by_error_stack_sql_query, (pattern,))
    else:
        # NEW
        # TODO Shall we use get_log() method instead of cursor.execute()?
        get_logger_severity_id_and_message_by_error_stack_sql_query = \
            ("SELECT logger_id, severity_id, message "
             "FROM logger.logger_view "
             "WHERE logger_id = %s "
             "ORDER BY timestamp DESC LIMIT 1;")
        cursor.execute(get_logger_severity_id_and_message_by_error_stack_sql_query, (error_logger_ids_dict[MYSQL],))

    get_logger_severity_id_and_message_by_error_stack_result = cursor.fetchone()
    if get_logger_severity_id_and_message_by_error_stack_result is not None:
        print(f"{PRINT_STARS}test_exception_with_payload() get_logger_severity_id_and_message_by_error_stack_result={get_logger_severity_id_and_message_by_error_stack_result}")  # noqa E501
        # TODO Didn't work in GHA, so I created this if. It should work always.
        assert get_logger_severity_id_and_message_by_error_stack_result[GET_LOGGER_SEVERITY_ID_AND_MESSAGE_BY_LOGGER_ID_SEVERITY_ID_COLUMN_IDX] >= LogMessageSeverity.ERROR.value  # noqa E501
        assert get_logger_severity_id_and_message_by_error_stack_result[GET_LOGGER_SEVERITY_ID_AND_MESSAGE_BY_LOGGER_ID_MESSAGE_IDX] == message  # noqa E501
    else:
        print(f"{PRINT_STARS}test_exception_with_payload() TODO get_logger_severity_id_and_message_by_error_stack_result is None")  # noqa E501

    logger.set_is_write_to_sql(original_is_write_to_sql)


def test_exception_with_only_logger_object(logger):
    stack_trace = ""
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(True)
    try:
        5 / 0
    except Exception as exception:
        error_logger_ids_dict = logger.error(object=exception)
        stack_trace = str(traceback.format_exception(
            type(exception), exception, exception.__traceback__))

    connection = get_test_connection()
    cursor = connection.cursor()

    TEST_EXCEPTION_WITH_ONLY_LOGGER_OBJECT_SEVERITY_ID_COLUMN_IDX = 0
    if error_logger_ids_dict is None:
        escaped_stack_trace = re.escape(stack_trace)
        pattern = f"%{escaped_stack_trace}%"
        test_exception_with_only_logger_object_sql_query = \
            ("SELECT severity_id FROM logger.logger_view "
             "WHERE error_stack LIKE %s "
             "ORDER BY timestamp DESC LIMIT 1;")
        # TODO Shall we user get_log() method instead of cursor.execute()?
        cursor.execute(test_exception_with_only_logger_object_sql_query, (pattern,))
    else:
        test_exception_with_only_logger_object_sql_query = \
            ("SELECT severity_id FROM logger.logger_view "
             "WHERE logger_id = %s "
             "ORDER BY timestamp DESC LIMIT 1;")
        # TODO Shall we user get_log() method instead of cursor.execute()?
        cursor.execute(test_exception_with_only_logger_object_sql_query, (error_logger_ids_dict[MYSQL],))

    test_exception_with_only_logger_object_sql_result = cursor.fetchone()
    if test_exception_with_only_logger_object_sql_result:
        assert test_exception_with_only_logger_object_sql_result[TEST_EXCEPTION_WITH_ONLY_LOGGER_OBJECT_SEVERITY_ID_COLUMN_IDX] >= LogMessageSeverity.ERROR.value  # noqa E501
    else:
        print(f"{PRINT_STARS}test_exception_with_only_logger_object() test_exception_with_only_logger_object_sql_result is None. TODO Fix it.")  # noqa E501

    logger.set_is_write_to_sql(original_is_write_to_sql)


def test_error(logger):
    object_to_insert9 = {
        'payload': 'payload from error python -object_9'

    }
    msg = "check for error with both object and message"
    logger.error(msg, object=object_to_insert9)

    result = get_log('payload', object_to_insert9)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.ERROR.value
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_start(logger):
    object_to_insert10 = {
        'payload': 'payload from start python -object_10'

    }
    msg = "check for start with both object and message"
    logger.start(msg, object=object_to_insert10)
    result = get_log('payload', object_to_insert10)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == StartEndEnum.START.value
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_end(logger):
    object_to_insert11 = {
        'payload': 'payload from end python -object_11'

    }
    msg = "check for end with both object and message"
    logger.end(msg, object=object_to_insert11)
    result = get_log('payload', object_to_insert11)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == StartEndEnum.END.value  # noqa E501
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_debug(logger):
    object_to_insert12 = {
        'payload': 'payload from debug python -object_12'

    }
    msg = "check for debug with both object and message"
    logger.debug(msg, object=object_to_insert12)
    result = get_log('payload', object_to_insert12)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.DEBUG.value
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_log(logger):
    object_to_insert13 = {
        'payload': 'payload from info python -object_13'

    }
    msg = "check for info with both object and message"
    logger.info(msg, object=object_to_insert13)
    result = get_log('payload', object_to_insert13)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.INFORMATION.value
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_init(logger):
    object_to_insert14 = {
        'payload': 'payload from init python -object_14'

    }
    msg = "check for init with both object and message"
    logger.init(msg, object=object_to_insert14)
    result = get_log('payload', object_to_insert14)
    assert result[GET_LOG_DEFAULT_SEVERITY_COLUMN_IDX] == LogMessageSeverity.INIT.value
    assert result[GET_LOG_DEFAULT_MESSAGE_COLUMN_IDX] == msg


def test_exception(logger):
    stack_trace = ""
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(True)
    try:
        5 / 0  # noqa
    except Exception as exception:
        logger.error("exception check", object=exception)
        stack_trace = str(traceback.format_exception(
            type(exception), exception, exception.__traceback__))

    connection = get_test_connection()
    cursor = connection.cursor()

    escaped_stack_trace = re.escape(stack_trace)
    pattern = f"%{escaped_stack_trace}%"
    TEST_EXCEPTION_SEVERITY_ID_COLUMN_IDX = 0
    TEST_EXCEPTION_MESSAGE_COLUMN_IDX = 1
    sql = ("SELECT severity_id,message FROM logger.logger_view "
           "WHERE error_stack LIKE %s ORDER BY timestamp DESC LIMIT 1;")
    # TODO Can we use get_log() method instead of cursor.execute()?
    cursor.execute(sql, (pattern,))
    result = cursor.fetchone()
    if result:
        assert result[TEST_EXCEPTION_SEVERITY_ID_COLUMN_IDX] >= LogMessageSeverity.ERROR.value
        assert result[TEST_EXCEPTION_MESSAGE_COLUMN_IDX] == "exception check"

    logger.set_is_write_to_sql(original_is_write_to_sql)


def test_check_function(logger):
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(True)
    # TODO Add such condition to all tests that use the database
    # if not DebugMode.is_write_to_sql:
    #     print("DebugMode.is_write_to_sql is True, skipping test_check_function")
    #     return
    connector_logger = ConnectorLogger()
    datetime_object = datetime.now()
    object_to_insert15 = {
        'payload': "check python",
        'component_id': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID,
        'a': 5,
        'b': 6,
        'datetime_object': datetime_object  # test inserting object
    }
    logger_start_logger_ids_dict = logger.start(object=object_to_insert15)
    print(f"test_check_function logger_ids_dict: {logger_start_logger_ids_dict}")

    # TODO Let's user our Connector class
    # connection = get_test_connection()
    connector_logger.get_connection(schema_name="logger")
    # cursor = connection.cursor()
    # I added logger_id for debugging
    # TODO Can we use get_log() method instead of sql_query
    GET_COMPONENT_ID_AND_RECORD_BY_LOGGER_ID_SQL_QUERY = """
    SELECT logger_id, component_id, record
    FROM logger.logger_view
    -- ignore other logs that may have been inserted.
    -- TODO: in all tests (This do not support multi users running tests on the same time)
    -- WHERE component_name = 'Logger Python'
    WHERE logger_id = %s;
    -- ORDER BY logger_id desc limit 1;
    """
    GET_COMPONENT_ID_AND_RECORD_LOGGER_ID_COLUMN_IDX = 0
    GET_COMPONENT_ID_AND_RECORD_COMPONENT_ID_COLUMN_IDX = 1
    GET_COMPONENT_ID_AND_RECORD_RECORD_COLUMN_IDX = 2

    # TODO Replace the 'MySQL' with const exported from the src constants
    # cursor.execute(sql_query, (logger_id_dict['MySQL'],))
    if logger_start_logger_ids_dict[MYSQL] is None:
        # pytest.skip("logger_start_logger_ids_dict[MYSQL] is None. TODO")
        assert False, "logger_start_logger_ids_dict[MYSQL] is None. TODO"
    execute_result = connector_logger.execute(GET_COMPONENT_ID_AND_RECORD_BY_LOGGER_ID_SQL_QUERY,
                                              (logger_start_logger_ids_dict[MYSQL],))
    print(f"execute_result: {execute_result}")
    # result = cursor.fetchone()
    result = connector_logger.fetchone()
    # TODO Assert that result is not empty

    print(f"result['logger_id']: {result[GET_COMPONENT_ID_AND_RECORD_LOGGER_ID_COLUMN_IDX]}")
    assert result[GET_COMPONENT_ID_AND_RECORD_COMPONENT_ID_COLUMN_IDX] == LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID

    print(f"result[LOGGER_ID_COLUMN_IDX]: {result[GET_COMPONENT_ID_AND_RECORD_LOGGER_ID_COLUMN_IDX]}")
    print(f"result[COMPONENT_ID_COLUMN_IDX]: {result[GET_COMPONENT_ID_AND_RECORD_COMPONENT_ID_COLUMN_IDX]}")

    received_record = json.loads(result[GET_COMPONENT_ID_AND_RECORD_RECORD_COLUMN_IDX])
    expected_record = {"a": "5", "b": 6, "datetime_object": datetime_object, "severity_name": "START"}
    # received_record may contain more fields than expected_record
    for k, v in expected_record.items():
        try:
            assert k in received_record
            assert received_record[k] == str(v)
        except AssertionError:
            print(f"object_to_insert15, key: {k}, expected: {v}, received: {received_record.get(k, received_record)}")  # noqa E501
            raise

    # TODO Uncomment
    RETURN_VALUE = 9
    object_to_insert16 = {
        'component_id': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID,
        'payload': "check python",
        'return': RETURN_VALUE,
    }
    # TODO Why logger.end() at this point?
    # TODO logger.end() cause problem with connection.commit()
    logger_end_logger_ids_dict = logger.end(object=object_to_insert16)
    print(f"object_to_insert16 logger_end_logger_id_dict: {logger_end_logger_ids_dict}")

    time.sleep(3)

    # Trying to resolve "Commands out of sync; you can't run this command now" error, when doing commit()
    # TODO Maybe we should create our commit() method which is trying to commit and if failed doing cursor.fetchall() and commit  # noqa E501
    # _ = cursor.fetchall()

    # sync the connection before querying
    # connection.commit()

    # connector_logger.commit()

    # cursor.execute(sql_query)
    # connector_logger.execute(sql_query)
    # TODO Replace 'MySQL' to MYSQL const/enum everywhere
    connector_logger.execute(GET_COMPONENT_ID_AND_RECORD_BY_LOGGER_ID_SQL_QUERY, (logger_end_logger_ids_dict[MYSQL],))

    # result = cursor.fetchone()
    result = connector_logger.fetchone()
    print(f"result: {result}")
    print(f"LOGGER_LOCAL_PYTHON_CODE_COMPONENT_ID: {LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID}")
    assert result[GET_COMPONENT_ID_AND_RECORD_COMPONENT_ID_COLUMN_IDX] == LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID

    received_record: dict[str, Any] = json.loads(result[GET_COMPONENT_ID_AND_RECORD_RECORD_COLUMN_IDX])
    print(f"received_record: {received_record}")
    expected_record: dict[str, Any] = {"return": RETURN_VALUE, "severity_name": "END"}
    print(f"expected_record: {expected_record}")
    # received_record may contain more fields than expected_record
    for k, v in expected_record.items():
        try:
            assert k in received_record
            assert received_record[k] == str(v)
        except AssertionError:
            print(f"object_to_insert16, key: {k}, expected: {v}, received: {received_record.get(k, received_record)}")  # noqa E501
            raise
    logger.set_is_write_to_sql(original_is_write_to_sql)


def test_check_init_component_enum(logger):
    object_to_insert17 = {
        # TODO Use const fields names instead of hard coded strings
        'payload': "check python init with component",
        'component_id': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID,
        'component_name': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME,
        "component_category": LoggerComponentEnum.ComponentCategory.Unit_Test.value,
        'testing_framework': LoggerComponentEnum.testingFramework.pytest.value,
    }
    logger.init(object=object_to_insert17)
    # TODO move the logger_id to the beginning
    select_clause = "component_name,component_category,testing_framework, logger_id"
    GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN_IDX = 0
    GET_LOG_SELECT_CLAUSE_COMPONENT_CATEGORY_COLUMN_IDX = 1
    GET_LOG_SELECT_CLAUSE_TESTING_FRAMEWORK_COLUMN_IDX = 2
    # TODO Shall we user the logger_ids_dict instead of get_log()?
    result = get_log('payload', object_to_insert17, select_clause=select_clause)
    assert result[GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN_IDX] == LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME  # noqa E501
    # TODO Uncomment
    assert result[GET_LOG_SELECT_CLAUSE_COMPONENT_CATEGORY_COLUMN_IDX] == LoggerComponentEnum.ComponentCategory.Unit_Test.value  # noqa E501
    assert result[GET_LOG_SELECT_CLAUSE_TESTING_FRAMEWORK_COLUMN_IDX] == LoggerComponentEnum.testingFramework.pytest.value  # noqa E501

    # Check logger.info() with a different message
    object_to_insert17['message'] = 'check if component saved'
    # test_check_init_component_enum_logger_id: int = logger.info(object_to_insert17['message'])
    test_check_init_component_enum_logger_id: int = logger.info(object_to_insert17['message'])
    print(f"test_check_init_component_enum_logger_id: {test_check_init_component_enum_logger_id}")  # noqa E501
    result17 = get_log('message', object_to_insert17, select_clause=select_clause)
    print(f"result17: {result17}")
    assert result17[GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN_IDX] == LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME  # noqa E501
    # TODO Uncomment
    assert result17[GET_LOG_SELECT_CLAUSE_COMPONENT_CATEGORY_COLUMN_IDX] == LoggerComponentEnum.ComponentCategory.Unit_Test.value  # noqa E501
    # TODO Fix the bug
    # assert result17[GET_LOG_SELECT_CLAUSE_TESTING_FRAMEWORK_COLUMN_IDX] == LoggerComponentEnum.testingFramework.pytest.value  # noqa E501


# Two logger instances
def test_check_init_two_different_loggers(logger):
    obj1 = {
        'component_id': TEST_COMPONENT_ID_1,
        'component_name': "check",
        'component_category': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_CATEGORY,
        "developer_email_address": LOGGER_LOCAL_PYTHON_TEST_DEVELOPER_EMAIL_ADDRESS,  # noqa E501
        "testing_framework": LoggerComponentEnum.testingFramework.pytest.value
    }
    obj2 = {
        'component_id': TEST_COMPONENT_ID_2,
        'component_name': "check2",
        'component_category': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_CATEGORY,
        "developer_email_address": LOGGER_LOCAL_PYTHON_TEST_DEVELOPER_EMAIL_ADDRESS,  # noqa E501
        "testing_framework": LoggerComponentEnum.testingFramework.pytest.value
    }
    logger1 = Logger.create_logger(object=obj1, level="info", ignore_cached_logger=True)
    logger2 = Logger.create_logger(object=obj2, level="info", ignore_cached_logger=True)
    logger1.set_is_write_to_sql(True)
    logger2.set_is_write_to_sql(True)

    msg1 = "check logger 1 " + str(datetime.now())
    logger1.info(msg1)
    GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN = 0
    comp1 = get_log('message', {'message': msg1}, select_clause="component_id")

    msg2 = "check logger 2 " + str(datetime.now())
    logger2.info(msg2)
    comp2 = get_log('message', {'message': msg2}, select_clause="component_id")

    assert comp1[GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN] == TEST_COMPONENT_ID_1
    assert comp2[GET_LOG_SELECT_CLAUSE_COMPONENT_NAME_COLUMN] == TEST_COMPONENT_ID_2


# TODO Move to python-sdk as we want to use it not only in logger
def test_obfuscate_log_dict():
    environment_name = get_environment_name()
    # TODO I'm not sure we want to play with prod1 environment, maybe "test"+random.randint(1, 1000000)
    os.environ["ENVIRONMENT_NAME"] = "prod1"

    log_dict = {
        "user_email": "user@example.com",
        "user_password": "supersecret",
        "login_time": "2024-06-03T12:34:56",
        "user_name": "John Doe",
    }
    expected_output = {
        "user_email": "***",
        "user_password": "***",
        "login_time": "2024-06-03T12:34:56",
        "user_name": "***",
    }
    assert obfuscate_log_dict(log_dict) == expected_output

    log_dict = {
        "user_email": "user@example.com",
        "details": {
            "token": "abcdef123456",
            "address": "123 Main St",
            "phone_number": "123-456-7890"
        },
        "component_id": 3
    }
    expected_output = {
        "user_email": "***",
        "details": {
            "token": "***",
            "address": "***",
            "phone_number": "***"
        },
        "component_id": 3
    }
    assert obfuscate_log_dict(log_dict) == expected_output

    log_dict = {
        "login_time": "2024-06-03T12:34:56",
        "status": "success",
        "session_id": "xyz123"
    }
    expected_output = {
        "login_time": "2024-06-03T12:34:56",
        "status": "success",
        "session_id": "xyz123"
    }
    assert obfuscate_log_dict(log_dict) == expected_output

    log_dict = {
        "user_email": "user@example.com",
        "login_time": "2024-06-03T12:34:56",
        "details": {
            "token": "abcdef123456",
            "address": "123 Main St",
            "name_last": "Doe",
            "test": "test"
        }
    }
    expected_output = {
        "user_email": "***",
        "login_time": "2024-06-03T12:34:56",
        "details": {
            "token": "***",
            "address": "***",
            "name_last": "***",
            "test": "test"
        }
    }
    assert obfuscate_log_dict(log_dict) == expected_output

    os.environ["ENVIRONMENT_NAME"] = environment_name


if __name__ == "__main__":
    # pytest.main(sys.argv[1:])
    test_check_init_two_different_loggers(logger)
