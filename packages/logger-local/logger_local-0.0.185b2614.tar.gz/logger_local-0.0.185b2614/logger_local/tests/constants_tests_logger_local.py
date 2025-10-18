from typing import Any
from logger_local.src.logger_component_enum import LoggerComponentEnum

LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID = 104
LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME = "Logger Local Python Test"
LOGGER_LOCAL_PYTHON_TEST_COMPONENT_CATEGORY = LoggerComponentEnum.ComponentCategory.Unit_Test.value  # noqa E501
LOGGER_LOCAL_PYTHON_TEST_DEVELOPER_EMAIL_ADDRESS = 'akiva.s@circ.zone'

LOGGER_LOCAL_PYTHON_TEST_LOGGER_OBJECT: dict[str, Any] = {
    'component_id': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_ID,
    'component_name': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_NAME,
    'component_category': LOGGER_LOCAL_PYTHON_TEST_COMPONENT_CATEGORY,
    'developer_email_address': LOGGER_LOCAL_PYTHON_TEST_DEVELOPER_EMAIL_ADDRESS
}

# TODO Shall we move this to logger-local package
LOGGER_STR = "logger_local.src.logger_local"  # It was "src.LoggerLocal"
