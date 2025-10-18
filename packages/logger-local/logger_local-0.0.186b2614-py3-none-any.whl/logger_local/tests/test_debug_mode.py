import logger_local.src.debug_mode as debug_mode
from python_sdk_remote.constants_src_mini_logger_and_logger import (
    LogMessageSeverity
)

# Disable environment variables to avoid import errors
debug_mode.DEFAULT_LOGGER_CONFIGURATION_JSON_PATH = None
debug_mode.DEFAULT_LOGGER_MINIMUM_SEVERITY = None
debug_mode.LOGGER_IS_WRITE_TO_SQL_ENV = None


def test_get_severity_level_information_no_exception():
    """Test __get_severity_level("Information") does not raise exception."""
    # This test verifies that the string "Information" is properly handled
    # and mapped to the LogMessageSeverity.INFORMATION enum value
    debug_mode_instance = debug_mode.DebugMode(
        logger_minimum_severity='Information')
    assert (debug_mode_instance.logger_minimum_severity ==
            LogMessageSeverity.INFORMATION.value)
