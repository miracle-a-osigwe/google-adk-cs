"""Web interfaces package for the customer service system."""

from .admin_interface import admin_app
from .customer_interface import customer_app
from .agent_interface import agent_app
from .api_interface import api_app

__all__ = ["admin_app", "customer_app", "agent_app", "api_app"]