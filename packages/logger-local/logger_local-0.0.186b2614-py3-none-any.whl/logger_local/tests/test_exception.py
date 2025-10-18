import re
import time

from logger_local.src.connector_logger import get_connection
from logger_local.src.logger_local import Logger
# from logger_local.src.message_severity import LogMessageSeverity
from python_sdk_remote.constants_src_mini_logger_and_logger import LogMessageSeverity
# from src.MessageSeverity import MessageSeverity
from .constants_tests_logger_local import LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT

# Replace all literals i.e. "Error" with const/enum
logger = Logger.create_logger(object=LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT,
                              level="Error",
                              ignore_cached_logger=True)

TEST_TWO_EXCEPTIONS_EXCEPTION_ONE_MESSAGE_PREFIX = "Exception #1 in test_two_exceptions()"  # noqa: E501
TEST_TWO_EXCEPTIONS_EXCEPTION_TWO_MESSAGE_PREFIX = "Exception #2 in test_two_exceptions()"  # noqa: E501


# Nested exceptions
def test_two_exceptions():
    logger.set_is_write_to_sql(True)
    try:
        try:
            print("Going to divide by zero")
            1 / 0
        except Exception as e:
            print("Calling logger.exception")
            logger_exception_logger_ids_dict = \
                logger.exception(TEST_TWO_EXCEPTIONS_EXCEPTION_ONE_MESSAGE_PREFIX,
                                 object=e)
            print("After calling logger.exception")
            print(f"logger_exception_logger_ids_dict={logger_exception_logger_ids_dict}")
        finally:
            logger.info("End test")
    except Exception as e:
        logger_error_logger_ids_dict = \
            logger.error(TEST_TWO_EXCEPTIONS_EXCEPTION_TWO_MESSAGE_PREFIX,
                         object=e)
        print(f"logger_error_logger_ids_dict={logger_error_logger_ids_dict}")

    _assert_tests(is_one_exception=False,
                  # sql_logger_ids=(logger_exception_logger_ids_dict[MYSQL] or None,
                  #                 logger_error_logger_ids_dict[MYSQL] or None,)
                  )


TEST_ONE_EXCEPTION_EXCEPTION_ONE_MESSAGE_PREFIX = "Exception #1 in test_one_exception()"  # noqa: E501
TEST_ONE_EXCEPTION_EXCEPTION_TWO_MESSAGE_PREFIX = "Exception #2 in test_one_exception()"


def test_one_exception():
    # TODO We should call a method to change the logger private attribute
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(True)
    try:
        try:
            1 / 0
        except Exception as e:
            logger_error1_logger_ids_dict = logger.error(TEST_ONE_EXCEPTION_EXCEPTION_ONE_MESSAGE_PREFIX,
                                                         object=e)
            print(f"logger_error1_logger_ids_dict={logger_error1_logger_ids_dict}")
            raise e
        finally:
            logger.info("End test")
            logger.set_is_write_to_sql(original_is_write_to_sql)
    except Exception as e:
        logger_error2_logger_ids_dict = \
            logger.error(TEST_ONE_EXCEPTION_EXCEPTION_TWO_MESSAGE_PREFIX,
                         object=e)
        print(f"logger_error2_logger_ids_dict={logger_error2_logger_ids_dict}")

    _assert_tests(is_one_exception=True,
                  # sql_logger_ids=(logger_error1_logger_ids_dict[MYSQL],
                  #                 logger_error2_logger_ids_dict[MYSQL],)
                  )


def _assert_tests(is_one_exception: bool,
                  # sql_logger_ids: tuple[int, int]
                  ) -> None:  # noqa: E501
    # print(f"_assert_tests is_one_exception={is_one_exception}, sql_logger_ids={sql_logger_ids}")  # noqa: E501
    time.sleep(5)  # wait for async write to sql
    original_is_write_to_sql = logger.get_is_write_to_sql()
    logger.set_is_write_to_sql(False)
    # TODO How can we update this test so it will also work when others are using the logger  # noqa: E501
    # TODO if is_run_alone:
    # TODO Do not use SELECT * as the view fields can change and we bring irrelevant data (Add a rule to identify it)  # noqa: E501
    # TODO Do not user ORDER BY logger_id as others might write to the log in parallel  # noqa: E501
    # TODO 2 or 3 rows?
    NUMBER_OF_RECORDS = 2
    # TODO Why do we need %s if it is constant?
    logger_error_and_higher_records_sql_query = f"SELECT * FROM logger.logger_view WHERE severity_id >= %s ORDER BY logger_id DESC LIMIT {NUMBER_OF_RECORDS}"  # noqa: E501
    connection = get_connection("logger")
    connection.commit()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(logger_error_and_higher_records_sql_query, (LogMessageSeverity.ERROR.value,))
    logger_errors_and_higher_records_sql_query_result = cursor.fetchall()
    print(f"logger_records_sql_query_result={logger_errors_and_higher_records_sql_query_result}")
    assert len(logger_errors_and_higher_records_sql_query_result) == NUMBER_OF_RECORDS

    # The line `assert result[1]['function_name'] == function_name` is performing an assertion check  # noqa: E501
    # in Python. It is verifying that the value stored in the 'function_name' key of the dictionary at  # noqa: E501
    # index 1 of the 'result' list is equal to the value stored in the 'function_name' variable.
    function_name = 'test_two_exceptions' if not is_one_exception else 'test_one_exception'
    assert logger_errors_and_higher_records_sql_query_result[1]['function_name'] == function_name
    assert logger_errors_and_higher_records_sql_query_result[0]['function_name'] == function_name

    if is_one_exception:
        assert logger_errors_and_higher_records_sql_query_result[1]['severity_id'] == LogMessageSeverity.ERROR.value
    else:
        assert logger_errors_and_higher_records_sql_query_result[1]['severity_id'] == LogMessageSeverity.EXCEPTION.value
    assert logger_errors_and_higher_records_sql_query_result[0]['severity_id'] == LogMessageSeverity.ERROR.value

    if is_one_exception:
        assert logger_errors_and_higher_records_sql_query_result[1]['message'] == TEST_ONE_EXCEPTION_EXCEPTION_ONE_MESSAGE_PREFIX  # noqa: E501
        assert logger_errors_and_higher_records_sql_query_result[0]['message'] == TEST_ONE_EXCEPTION_EXCEPTION_TWO_MESSAGE_PREFIX  # noqa: E501
    else:
        assert logger_errors_and_higher_records_sql_query_result[1]['message'] == TEST_TWO_EXCEPTIONS_EXCEPTION_ONE_MESSAGE_PREFIX  # noqa: E501
        assert logger_errors_and_higher_records_sql_query_result[0]['message'] == TEST_TWO_EXCEPTIONS_EXCEPTION_TWO_MESSAGE_PREFIX  # noqa: E501

    assert logger_errors_and_higher_records_sql_query_result[1]['error_stack'].startswith(r"['Traceback (most recent call last):\n'")  # noqa: E501
    assert logger_errors_and_higher_records_sql_query_result[0]['error_stack'].startswith(r"['Traceback (most recent call last):\n'")  # noqa: E501

    assert logger_errors_and_higher_records_sql_query_result[1]['error_stack'].endswith(r"'ZeroDivisionError: division by zero\n']")  # noqa: E501
    assert logger_errors_and_higher_records_sql_query_result[0]['error_stack'].endswith(r"'ZeroDivisionError: division by zero\n']")  # noqa: E501

    assert len(set(re.findall(r'line \d+', logger_errors_and_higher_records_sql_query_result[1]['error_stack']))) == 1  # noqa: E501
    assert len(set(re.findall(r'line \d+', logger_errors_and_higher_records_sql_query_result[0]['error_stack']))) == 3 - int(is_one_exception)  # noqa: E501

    logger.set_is_write_to_sql(original_is_write_to_sql)
