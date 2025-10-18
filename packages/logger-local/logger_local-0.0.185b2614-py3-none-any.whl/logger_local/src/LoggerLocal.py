# Backward compatibility module
from .logger_local import Logger
from .logger_component_enum import LoggerComponentEnum
from .meta_logger import MetaLogger

# Export LOGGER_COMPONENT_ID for backward compatibility
LOGGER_COMPONENT_ID = 1  # Default component ID for tests

__all__ = ['Logger', 'LoggerComponentEnum', 'LOGGER_COMPONENT_ID', 'MetaLogger']
