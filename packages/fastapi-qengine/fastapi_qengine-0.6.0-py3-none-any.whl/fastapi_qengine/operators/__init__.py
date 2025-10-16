"""Operators module initialization."""

# Import global operator registry
from .base import global_operator_registry


# For backwards compatibility, provide empty registries
# (operators are now handled globally)
LOGICAL_OPERATORS = {}
COMPARISON_OPERATORS = {}


__all__ = [
    "global_operator_registry",
    "LOGICAL_OPERATORS",  # Kept for backwards compatibility
    "COMPARISON_OPERATORS",  # Kept for backwards compatibility
]
