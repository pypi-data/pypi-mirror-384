#
# config/__init__.py
#
"""
Configuration module for supsrc.

Re-exports all configuration models and loading functions for backwards compatibility.
"""

from __future__ import annotations

# Re-export all config models and functions
from supsrc.config.models import (
    ConfigurationError,
    GlobalConfig,
    InactivityRuleConfig,
    LLMConfig,
    ManualRuleConfig,
    RepositoryConfig,
    RuleConfig,
    SaveCountRuleConfig,
    SupsrcConfig,
    load_config,
    load_repository_config,
)

__all__ = [
    "ConfigurationError",
    "GlobalConfig",
    "InactivityRuleConfig",
    "LLMConfig",
    "ManualRuleConfig",
    "RepositoryConfig",
    "RuleConfig",
    "SaveCountRuleConfig",
    "SupsrcConfig",
    "load_config",
    "load_repository_config",
]
