#
# supsrc/exceptions.py
#
"""
Supsrc exceptions using Foundation's error system.
"""

from provide.foundation.errors import FoundationError
from provide.foundation.errors.config import ConfigurationError as BaseConfigurationError


class SupsrcError(FoundationError):
    """Base class for all supsrc application specific errors."""

    pass


# Configuration exceptions - these now inherit from Foundation's config errors
class ConfigurationError(BaseConfigurationError, SupsrcError):
    """Configuration-related errors using Foundation's error system."""

    pass


class ConfigFileNotFoundError(ConfigurationError, FileNotFoundError):
    """Configuration file not found."""

    pass


class ConfigParsingError(ConfigurationError):
    """Configuration file parsing errors."""

    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation errors."""

    pass


class PathValidationError(ConfigValidationError):
    """Path validation errors."""

    pass


class DurationValidationError(ConfigValidationError):
    """Duration validation errors."""

    pass


# Monitoring exceptions
class MonitoringError(SupsrcError):
    """Base class for monitoring-related errors."""

    pass


class MonitoringSetupError(MonitoringError):
    """Monitoring setup errors."""

    pass


# Export all exceptions for backward compatibility
__all__ = [
    "ConfigFileNotFoundError",
    "ConfigParsingError",
    "ConfigValidationError",
    "ConfigurationError",
    "DurationValidationError",
    "MonitoringError",
    "MonitoringSetupError",
    "PathValidationError",
    "SupsrcError",
]

# 🔼⚙️
