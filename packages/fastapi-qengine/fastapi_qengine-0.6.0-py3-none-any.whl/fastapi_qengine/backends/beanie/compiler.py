"""
Beanie query compiler.

This module contains the BeanieQueryCompiler class for compiling queries to Beanie/PyMongo format.
"""

from typing import cast

from fastapi_qengine.core.compiler_base import QueryAdapter, compile_condition_helper
from fastapi_qengine.core.errors import CompilerError
from fastapi_qengine.core.types import (
    ASTNode,
    FieldCondition,
    FieldsNode,
    FilterAST,
    LogicalCondition,
    LogicalOperator,
    OrderNode,
)

from ...operators.base.registry import (
    ComparisonCompiler,
    LogicalCompiler,
    global_operator_registry,
)
from .adapter import BeanieQueryAdapter


class BeanieQueryCompiler:
    """Query compiler for Beanie/PyMongo backend."""

    def __init__(self) -> None:
        self.backend_name: str = "beanie"
        self.adapter: BeanieQueryAdapter | None = None

    def create_base_query(self) -> QueryAdapter:
        """Create the base query adapter for Beanie."""
        self.adapter = BeanieQueryAdapter()
        return self.adapter

    def apply_where(self, query: QueryAdapter, where_node: ASTNode) -> QueryAdapter:
        """Apply where conditions to the query."""
        condition: object = self.compile_condition(condition=where_node)
        return query.add_where_condition(condition)

    def apply_order(self, query: QueryAdapter, order_nodes: list[OrderNode]) -> QueryAdapter:
        """Apply ordering to the query."""
        for order_node in order_nodes:
            query = query.add_sort(order_node.field, order_node.ascending)
        return query

    def apply_fields(self, query: QueryAdapter, fields_node: FieldsNode) -> QueryAdapter:
        """Apply field projection to the query."""
        return query.set_projection(fields_node.fields)

    def finalize_query(self, query: QueryAdapter) -> dict[str, object]:
        """Finalize the query and return MongoDB query components."""
        return query.build()

    def compile_field_condition(self, condition: FieldCondition) -> dict[str, object]:
        """Compile a field condition to MongoDB format."""
        compiler: ComparisonCompiler | None = cast(
            ComparisonCompiler,
            global_operator_registry.get_compiler(condition.operator.value, self.backend_name),
        )
        if not compiler:
            raise CompilerError(f"Unsupported operator: {condition.operator}")

        return compiler(condition.field, condition.value)

    def compile_logical_condition(self, condition: LogicalCondition) -> dict[str, list[object]]:
        """Compile a logical condition to MongoDB format."""
        # Ensure operator_name is a string for the registry lookup
        op: LogicalOperator = getattr(condition.operator, "value", condition.operator)
        if not isinstance(op, str):
            raise CompilerError(f"Unsupported logical operator type: {type(condition.operator)!r}")
        operator_name: str = op

        compiler: LogicalCompiler = cast(
            LogicalCompiler,
            global_operator_registry.get_compiler(operator_name, self.backend_name),
        )
        if not compiler:
            raise CompilerError(f"Unsupported logical operator: {condition.operator}")

        # Compile nested conditions
        compiled_conditions: list[object] = [
            self.compile_condition(nested_condition) for nested_condition in condition.conditions
        ]

        return compiler(compiled_conditions)

    def compile_condition(self, condition: ASTNode) -> object:
        """Compile a condition node to backend-specific format."""
        return compile_condition_helper(self, condition)

    def supports_backend(self, backend_type: str) -> bool:
        """Check if this compiler supports the given backend."""
        return backend_type == self.backend_name

    def build_query(self, ast: FilterAST) -> dict[str, object]:
        """
        Build a backend-specific query from a FilterAST.

        Args:
            ast: The Abstract Syntax Tree representing the filter.

        Returns:
            A backend-specific query object.
        """
        return self.compile(ast)

    def compile(self, ast: FilterAST) -> dict[str, object]:
        """
        Compile FilterAST to MongoDB query components.

        Args:
            ast: FilterAST to compile

        Returns:
            Dictionary with query components (filter, sort, projection)
        """
        query: QueryAdapter = self.create_base_query()

        # Apply where conditions
        if ast.where:
            query = self.apply_where(query, where_node=ast.where)

        # Apply ordering
        if ast.order:
            query = self.apply_order(query, order_nodes=ast.order)

        # Apply field projection
        if ast.fields:
            query = self.apply_fields(query, fields_node=ast.fields)

        return self.finalize_query(query)
