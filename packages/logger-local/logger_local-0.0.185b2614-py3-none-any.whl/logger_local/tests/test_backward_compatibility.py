# TODO Test sending logger_object with developer_email instead of developer_email_address  # noqa E501

from typing import Any
from ..src.logger_local import Logger
from ..src.constants_src_logger_local import LOGGER_LOCAL_PYTHON_CODE_COMPONENT_ID  # noqa E501


def test_logger_object_with_old_developer_email_field():
    # TODO Change to upper case
    logger_object_with_old_developer_email_field: dict[str, Any] = {
        'developer_email': "check old developer_email_field",
        # TODO Shall we change component_id to componentId?
        'component_id': LOGGER_LOCAL_PYTHON_CODE_COMPONENT_ID,
        'component_name': 'Test Component',
        'component_category': 'Unit-Test',
        # 'datetime_object': datetime_object  # test inserting object
    }
    logger = Logger.create_logger(object=logger_object_with_old_developer_email_field)
    logger_id_dict = logger.start(object=logger_object_with_old_developer_email_field)
    print("logger_id_dict: ", logger_id_dict)
    # TODO Do we need this?
    assert True
