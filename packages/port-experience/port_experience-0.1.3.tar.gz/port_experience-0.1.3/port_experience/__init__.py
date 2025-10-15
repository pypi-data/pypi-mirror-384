"""
Port One-Click Middleware
==========================

A Python middleware service for managing Port.io resources including 
blueprints, actions, mappings, and widgets.

This package provides an interactive CLI and programmatic API to create, 
update, and synchronize Port.io configurations from local JSON files.

Main Components:
    - BasePortManager: Shared authentication and API request handling
    - PortBlueprintManager: Manages Port.io blueprints
    - PortActionManager: Manages Port.io actions
    - PortMappingManager: Manages Port.io integrations and mappings
    - PortWidgetManager: Manages Port.io dashboard widgets
    - BlueprintTreeManager: Handles blueprint dependency resolution

Example:
    >>> from port_experience import PortBlueprintManager
    >>> manager = PortBlueprintManager(client_id="...", client_secret="...")
    >>> manager.setup_all_blueprints("path/to/blueprints")
"""

# Version of the port-experience package
__version__ = "0.1.3"
__author__ = "CS - SA Team"
__email__ = "cs-sa@port.io"
__license__ = "MIT"

# Import main managers for easy access
from port_experience.managers import (
    BasePortManager,
)
from port_experience.managers.blueprint_manager import PortBlueprintManager
from port_experience.managers.action_manager import PortActionManager
from port_experience.managers.mapping_manager import PortMappingManager
from port_experience.managers.widget_manager import PortWidgetManager
from port_experience.managers.blueprint_tree_manager import BlueprintTreeManager

# Define what gets imported with "from port_experience import *"
__all__ = [
    "__version__",
    "BasePortManager",
    "PortBlueprintManager",
    "PortActionManager",
    "PortMappingManager",
    "PortWidgetManager",
    "BlueprintTreeManager",
]

