"""
Global operators module.

This module provides global operator definitions and backend-specific compilation.
"""

from .registry import GlobalOperatorRegistry, global_operator_registry

__all__ = ["GlobalOperatorRegistry", "global_operator_registry"]
