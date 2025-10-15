"""
CLI enums for type safety and validation.

Provides strongly-typed enum values for CLI parameters to ensure
consistency and enable better validation across all commands.
"""

from enum import Enum


class AISystem(str, Enum):
    """Available AI systems for installation."""

    CLAUDE_CODE = "claude-code"
    CLAUDE_DESKTOP = "claude-desktop"
    AUGGIE = "auggie"
    UNIVERSAL = "universal"


class OutputFormat(str, Enum):
    """Output format options for various commands."""

    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    PLAIN = "plain"
    TABLE = "table"
    LIST = "list"
    HTML = "html"


class MemoryType(str, Enum):
    """Memory classification types following cognitive psychology model."""

    SEMANTIC = "semantic"  # Facts, specifications, identity info (never expires)
    PROCEDURAL = "procedural"  # Instructions, processes, patterns (never expires)
    PREFERENCE = "preference"  # Team/user preferences, conventions (never expires)
    EPISODIC = "episodic"  # Project decisions, events, experiences (30 days)
    WORKING = "working"  # Current tasks, immediate priorities (1 day)
    SENSORY = "sensory"  # UI/UX observations, system behavior (6 hours)


class DiagnosticCheck(str, Enum):
    """Diagnostic check types for the doctor command."""

    CONNECTION = "connection"
    TOOLS = "tools"
    SCHEMA = "schema"
    PERFORMANCE = "performance"
    CONFIG = "config"
    ALL = "all"


class RecallStrategy(str, Enum):
    """Memory recall strategies."""

    AUTO = "auto"
    KEYWORD = "keyword"
    ENTITY = "entity"
    TEMPORAL = "temporal"


class InstallationMode(str, Enum):
    """Installation modes for integrations."""

    AUTO = "auto"
    PIPX = "pipx"
    HOME = "home"
    WRAPPER = "wrapper"
    STANDALONE = "standalone"


__all__ = [
    "AISystem",
    "DiagnosticCheck",
    "InstallationMode",
    "MemoryType",
    "OutputFormat",
    "RecallStrategy",
]
