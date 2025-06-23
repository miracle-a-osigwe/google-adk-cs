"""Admin interface package."""

from .admin_api import admin_app
from .config_manager import ConfigManager

__all__ = ["admin_app", "ConfigManager"]