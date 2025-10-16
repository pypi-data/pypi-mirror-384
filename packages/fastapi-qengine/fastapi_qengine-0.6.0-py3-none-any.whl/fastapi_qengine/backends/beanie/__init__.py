"""
Beanie backend module initialization.

This module provides the Beanie backend for fastapi-qengine.
"""

# Import operators to register them
from . import operators

# Import main classes and functions
from .adapter import BeanieQueryAdapter
from .compiler import BeanieQueryCompiler
from .engine import BeanieQueryEngine

__all__ = [
    "BeanieQueryAdapter",
    "BeanieQueryCompiler",
    "BeanieQueryEngine",
    "operators",
]
