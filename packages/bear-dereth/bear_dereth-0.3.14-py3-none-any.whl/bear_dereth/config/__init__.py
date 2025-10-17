"""Config and settings management utilities for Bear Utils."""

from ._base_settings import BaseSettingHandler, TableWrapper
from .config_manager import ConfigManager
from .dir_manager import (
    DirectoryManager,
    clear_temp_directory,
    get_cache_path,
    get_config_path,
    get_local_config_path,
    get_settings_path,
    get_temp_path,
)
from .quick_settings import SimpleSettingsManager
from .settings_manager import BearSettings, SettingsManager, StorageChoices

__all__ = [
    "BaseSettingHandler",
    "BearSettings",
    "ConfigManager",
    "DirectoryManager",
    "SettingsManager",
    "SimpleSettingsManager",
    "StorageChoices",
    "TableWrapper",
    "clear_temp_directory",
    "get_cache_path",
    "get_config_path",
    "get_local_config_path",
    "get_settings_path",
    "get_temp_path",
]
