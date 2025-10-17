"""
Reforge Python client library.

This module provides access to the Reforge configuration and feature flag service.

Main components:
- ReforgeSDK: The main SDK for interacting with Reforge
- Options: Configuration options for the SDK
- Context: Context information for evaluating configs and feature flags

Re-exported Protocol Buffer types:
- ConfigValue: Represents a configuration value
- StringList: Represents a list of strings
- ProtoContext: Protocol buffer Context class
- ContextSet: Collection of contexts
- ContextShape: Shape information for contexts
- LogLevel: Enumeration of log levels
- Json: Represents JSON data in configuration values
- Schema: Represents schema validation for configuration values
"""

from typing import Optional

from . import _internal_logging
from .options import Options as Options
from .sdk import ReforgeSDK as ReforgeSDK
from importlib.metadata import version
from .read_write_lock import ReadWriteLock as _ReadWriteLock
from .context import Context, NamedContext
from .feature_flag_sdk import FeatureFlagSDK
from .config_sdk import ConfigSDK
from .constants import (
    ConfigValueType,
    ContextDictType,
    ContextDictOrContext,
    NoDefaultProvided,
)

# Re-export Protocol Buffer types for easier access
import prefab_pb2
from prefab_pb2 import (
    ConfigValue,
    StringList,
    Context as ProtoContext,
    ContextSet,
    ContextShape,
    LogLevel,
    Json,
    Schema,
)

log = _internal_logging.InternalLogger(__name__)


__base_sdk: Optional[ReforgeSDK] = None
__options: Optional[Options] = None
__lock = _ReadWriteLock()


def set_options(options: Options) -> None:
    """Configure the SDK. SDK will be instantiated lazily with these options. Setting them again will have no effect unless reset_instance is called"""
    global __options
    with __lock.write_locked():
        __options = options


def get_sdk() -> ReforgeSDK:
    """Returns the singleton instance of the SDK. Created if needed using the options set by set_options"""
    global __base_sdk
    with __lock.read_locked():
        if __base_sdk:
            return __base_sdk

    with __lock.write_locked():
        if not __options:
            raise Exception("Options has not been set")
        if not __base_sdk:
            log.info(f"Initializing Reforge SDK version {version('reforge-python')}")
            __base_sdk = ReforgeSDK(__options)
            return __base_sdk


def reset_instance() -> None:
    """clears the singleton SDK instance so it will be recreated on the next get() call"""
    global __base_sdk
    global __lock
    __lock = _ReadWriteLock()
    old_sdk = __base_sdk
    __base_sdk = None
    if old_sdk:
        old_sdk.close()
