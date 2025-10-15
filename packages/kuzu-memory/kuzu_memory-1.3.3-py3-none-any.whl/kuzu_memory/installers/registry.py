"""
Installer Registry for KuzuMemory

Manages available installers and provides lookup functionality.
"""

import logging
from pathlib import Path

from .auggie import AuggieInstaller
from .base import BaseInstaller
from .claude_desktop import (
    ClaudeDesktopHomeInstaller,
    ClaudeDesktopPipxInstaller,
    SmartClaudeDesktopInstaller,
)
from .claude_hooks import ClaudeHooksInstaller
from .cursor_installer import CursorInstaller
from .universal import UniversalInstaller
from .vscode_installer import VSCodeInstaller
from .windsurf_installer import WindsurfInstaller

logger = logging.getLogger(__name__)


class InstallerRegistry:
    """
    Registry of available installers for different AI systems.

    Provides lookup and discovery functionality for installers.
    """

    def __init__(self):
        """Initialize the installer registry."""
        self._installers: dict[str, type[BaseInstaller]] = {}
        self._register_builtin_installers()

    def _register_builtin_installers(self):
        """Register built-in installers."""
        # AI System Installers (ONE PATH per system)
        self.register("auggie", AuggieInstaller)
        self.register("claude-code", ClaudeHooksInstaller)  # Claude Code with hooks/MCP
        self.register(
            "claude-desktop", SmartClaudeDesktopInstaller
        )  # Smart auto-detection
        self.register("universal", UniversalInstaller)

        # MCP-specific installers (Priority 1)
        self.register("cursor", CursorInstaller)  # Cursor IDE MCP
        self.register("vscode", VSCodeInstaller)  # VS Code with Claude extension MCP
        self.register("windsurf", WindsurfInstaller)  # Windsurf IDE MCP

        # Legacy aliases (DEPRECATED - will show warnings)
        # These are kept for backward compatibility only
        self.register("claude", ClaudeHooksInstaller)  # DEPRECATED: Use claude-code
        self.register("claude-mcp", ClaudeHooksInstaller)  # DEPRECATED: Use claude-code
        self.register(
            "claude-desktop-pipx", ClaudeDesktopPipxInstaller
        )  # DEPRECATED: Use claude-desktop
        self.register(
            "claude-desktop-home", ClaudeDesktopHomeInstaller
        )  # DEPRECATED: Use claude-desktop --mode=home
        self.register("generic", UniversalInstaller)  # DEPRECATED: Use universal

    def register(self, name: str, installer_class: type[BaseInstaller]):
        """
        Register an installer.

        Args:
            name: Name/identifier for the installer
            installer_class: Installer class
        """
        if not issubclass(installer_class, BaseInstaller):
            raise ValueError("Installer class must inherit from BaseInstaller")

        self._installers[name.lower()] = installer_class
        logger.debug(f"Registered installer: {name} -> {installer_class.__name__}")

    def get_installer(self, name: str, project_root: Path) -> BaseInstaller | None:
        """
        Get installer instance by name.

        Args:
            name: Name of the installer
            project_root: Project root directory

        Returns:
            Installer instance or None if not found
        """
        installer_class = self._installers.get(name.lower())
        if installer_class:
            return installer_class(project_root)
        return None

    def list_installers(self) -> list[dict[str, str]]:
        """
        List all available installers.

        Returns:
            List of installer information dictionaries
        """
        installers = []
        seen_classes = set()

        for name, installer_class in self._installers.items():
            # Avoid duplicates for aliases
            if installer_class in seen_classes:
                continue
            seen_classes.add(installer_class)

            # Create temporary instance to get info
            temp_instance = installer_class(Path("."))

            installers.append(
                {
                    "name": name,
                    "ai_system": temp_instance.ai_system_name,
                    "description": temp_instance.description,
                    "class": installer_class.__name__,
                }
            )

        return sorted(installers, key=lambda x: x["name"])

    def get_installer_names(self) -> list[str]:
        """
        Get list of all installer names.

        Returns:
            List of installer names
        """
        return sorted(self._installers.keys())

    def has_installer(self, name: str) -> bool:
        """
        Check if installer exists.

        Args:
            name: Installer name

        Returns:
            True if installer exists
        """
        return name.lower() in self._installers


# Global registry instance
_registry = InstallerRegistry()


def get_installer(name: str, project_root: Path) -> BaseInstaller | None:
    """
    Get installer instance by name.

    Args:
        name: Name of the installer
        project_root: Project root directory

    Returns:
        Installer instance or None if not found
    """
    return _registry.get_installer(name, project_root)


def list_installers() -> list[dict[str, str]]:
    """
    List all available installers.

    Returns:
        List of installer information dictionaries
    """
    return _registry.list_installers()


def get_installer_names() -> list[str]:
    """
    Get list of all installer names.

    Returns:
        List of installer names
    """
    return _registry.get_installer_names()


def has_installer(name: str) -> bool:
    """
    Check if installer exists.

    Args:
        name: Installer name

    Returns:
        True if installer exists
    """
    return _registry.has_installer(name)


def register_installer(name: str, installer_class: type[BaseInstaller]):
    """
    Register a custom installer.

    Args:
        name: Name/identifier for the installer
        installer_class: Installer class
    """
    _registry.register(name, installer_class)
