# Logger Local Package
from .src.LoggerLocal import Logger, LoggerComponentEnum, LOGGER_COMPONENT_ID
from .src.meta_logger import MetaLogger, ABCMetaLogger, module_wrapper

# Create a MetaLogger module for backward compatibility
class MetaLoggerModule:
    def __init__(self):
        self.MetaLogger = MetaLogger
        self.ABCMetaLogger = ABCMetaLogger
        self.module_wrapper = module_wrapper

# Create a LoggerComponentEnum module for backward compatibility
class LoggerComponentEnumModule:
    def __init__(self):
        self.LoggerComponentEnum = LoggerComponentEnum

# Create a LoggerLocal module for backward compatibility
class LoggerLocalModule:
    def __init__(self):
        self.Logger = Logger
        self.LoggerComponentEnum = LoggerComponentEnum
        self.LOGGER_COMPONENT_ID = LOGGER_COMPONENT_ID

# Make MetaLogger, LoggerComponentEnum, and LoggerLocal available as both direct import and module.class import
import sys
sys.modules[__name__ + '.MetaLogger'] = MetaLoggerModule()
sys.modules[__name__ + '.LoggerComponentEnum'] = LoggerComponentEnumModule()
sys.modules[__name__ + '.LoggerLocal'] = LoggerLocalModule()

__all__ = ['Logger', 'LoggerComponentEnum', 'LOGGER_COMPONENT_ID', 'MetaLogger', 'ABCMetaLogger', 'module_wrapper']
