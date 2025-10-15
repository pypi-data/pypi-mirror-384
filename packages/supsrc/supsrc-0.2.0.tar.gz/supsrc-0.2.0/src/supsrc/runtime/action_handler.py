# src/supsrc/runtime/action_handler.py

"""
Legacy import module for ActionHandler.

This module provides backward compatibility by re-exporting the RuntimeWorkflow
class as ActionHandler from the new workflow package structure.
"""

from __future__ import annotations

# Import from new package structure for backward compatibility
from supsrc.runtime.workflow.executor import RuntimeWorkflow

# Maintain backward compatibility with the old class name
ActionHandler = RuntimeWorkflow

__all__ = ["ActionHandler"]
