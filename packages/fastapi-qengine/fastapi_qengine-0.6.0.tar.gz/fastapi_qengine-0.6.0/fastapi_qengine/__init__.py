"""
FastAPI Query Engine - Advanced filtering for FastAPI applications.

A powerful query engine inspired by Loopback 4's filtering system,
providing flexible URL-based filtering with support for complex queries,
operators, and automatic OpenAPI documentation generation.
"""

from importlib.metadata import version

# Core imports
# Backend-specific imports
from .backends import BeanieQueryEngine
from .core import (
    FilterAST,
    FilterInput,
    ParseError,
    QEngineConfig,
    QEngineError,
    SecurityError,
    SecurityPolicy,
    ValidationError,
    create_response_model,
    default_config,
)

# Main interface
from .dependency import create_qe_dependency, process_filter_to_ast


__all__ = [
    # Main interface
    # Dependency helper
    "create_qe_dependency",
    # Pipeline utility
    "process_filter_to_ast",
    # Core types
    "FilterAST",
    "FilterInput",
    "QEngineConfig",
    "SecurityPolicy",
    "default_config",
    # Errors
    "QEngineError",
    "ParseError",
    "ValidationError",
    "SecurityError",
    # Backend utilities
    "BeanieQueryEngine",
    # Response Model Factory
    "create_response_model",
]


def main():
    print("fastapi-qengine: Advanced query engine for FastAPI")
    print(f"Version: {version('fastapi-qengine')}")
    print("For usage examples, see: https://github.com/urielcuriel/fastapi-qengine")


if __name__ == "__main__":
    main()
