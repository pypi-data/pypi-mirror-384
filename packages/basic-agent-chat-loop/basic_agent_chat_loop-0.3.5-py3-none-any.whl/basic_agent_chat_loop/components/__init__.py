"""
Components for Basic Agent Chat Loop.

This package contains modular components extracted from the main chat loop
for better maintainability and testability.
"""

from .agent_loader import (
    extract_agent_metadata,
    load_agent_module,
    load_environment_variables,
)
from .alias_manager import AliasManager
from .audio_notifier import AudioNotifier
from .config_wizard import ConfigWizard
from .dependency_manager import DependencyManager
from .display_manager import DisplayManager
from .template_manager import TemplateManager
from .token_tracker import TokenTracker
from .ui_components import Colors, StatusBar

__all__ = [
    "AudioNotifier",
    "Colors",
    "ConfigWizard",
    "StatusBar",
    "TokenTracker",
    "TemplateManager",
    "DisplayManager",
    "AliasManager",
    "DependencyManager",
    "load_environment_variables",
    "load_agent_module",
    "extract_agent_metadata",
]
