"""
Global operators registry for defining operators with their semantics.

This module provides a way to define operators globally, with backends registering
their specific compilation logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from fastapi_qengine.core.types import ComparisonOperator, LogicalOperator


class OperatorType(Enum):
    """Type of operator."""

    COMPARISON = "comparison"
    LOGICAL = "logical"
    CUSTOM = "custom"


@dataclass
class OperatorDefinition:
    """Definition of an operator with its semantics."""

    name: str
    operator_type: OperatorType
    description: str = ""


class ComparisonCompiler(Protocol):
    """Protocol for comparison operator compilation functions."""

    def __call__(self, field: str, value: object) -> dict[str, object]: ...


class LogicalCompiler(Protocol):
    """Protocol for logical operator compilation functions."""

    def __call__(self, conditions: list[object]) -> dict[str, list[object]]: ...


OperatorCompiler = ComparisonCompiler | LogicalCompiler


class GlobalOperatorRegistry:
    """Global registry for operators and their backend-specific compilations."""

    def __init__(self):
        self._operators: dict[str, OperatorDefinition] = {}
        self._compilers: dict[
            str, dict[str, OperatorCompiler]
        ] = {}  # operator -> backend -> compiler

    def define_operator(
        self, name: str, operator_type: OperatorType, description: str = ""
    ) -> None:
        """Define a global operator."""
        if name in self._operators:
            raise ValueError(f"Operator '{name}' already defined")
        self._operators[name] = OperatorDefinition(name, operator_type, description)

    def register_compiler(
        self, operator_name: str, backend: str, compiler: OperatorCompiler
    ) -> None:
        """Register a compilation function for an operator and backend."""
        if operator_name not in self._operators:
            raise ValueError(f"Operator '{operator_name}' not defined")

        if operator_name not in self._compilers:
            self._compilers[operator_name] = {}

        self._compilers[operator_name][backend] = compiler

    def get_compiler(self, operator_name: str, backend: str) -> OperatorCompiler | None:
        """Get the compiler for an operator and backend."""
        return self._compilers.get(operator_name, {}).get(backend)

    def is_supported(self, operator_name: str, backend: str) -> bool:
        """Check if an operator is supported for a backend."""
        return (
            operator_name in self._compilers
            and backend in self._compilers[operator_name]
        )

    def list_operators(self, backend: str | None = None) -> list[str]:
        """List all defined operators, optionally filtered by backend support."""
        if backend is None:
            return list(self._operators.keys())
        return [
            name for name in self._operators.keys() if self.is_supported(name, backend)
        ]

    def get_operator_definition(self, name: str) -> OperatorDefinition | None:
        """Get the definition of an operator."""
        return self._operators.get(name)


# Global instance
global_operator_registry = GlobalOperatorRegistry()


# Define built-in operators
def _define_builtin_operators():
    """Define all built-in operators."""
    # Comparison operators
    for op in ComparisonOperator:
        global_operator_registry.define_operator(op.value, OperatorType.COMPARISON)

    # Logical operators
    for op in LogicalOperator:
        global_operator_registry.define_operator(op.value, OperatorType.LOGICAL)

    # Custom operators (built-in ones)
    global_operator_registry.define_operator(
        "$text", OperatorType.CUSTOM, "Text search operator"
    )
    global_operator_registry.define_operator(
        "$geoWithin", OperatorType.CUSTOM, "Geospatial within operator"
    )
    global_operator_registry.define_operator(
        "$near", OperatorType.CUSTOM, "Geospatial proximity operator"
    )


_define_builtin_operators()
