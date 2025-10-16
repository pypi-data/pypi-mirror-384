"""
Base compiler class and interfaces.
"""

from typing import Protocol

from .errors import CompilerError
from .types import (
    ASTNode,
    FieldCondition,
    FieldsNode,
    FilterAST,
    LogicalCondition,
    OrderNode,
    T,
)


class QueryAdapter(Protocol):
    """Protocol for different query adapter types."""

    def add_where_condition(self, condition: object) -> "QueryAdapter":
        """Add a where condition to the query."""
        ...

    def add_sort(self, field: str, ascending: bool = True) -> "QueryAdapter":
        """Add sorting to the query."""
        ...

    def set_projection(self, fields: dict[str, int]) -> "QueryAdapter":
        """Set field projection."""
        ...

    def build(self) -> dict[str, object]:
        """Build the final query object."""
        ...


class BaseQueryCompiler(Protocol[T]):
    """Protocol for query compilers implementing Template Method pattern."""

    backend_name: str

    def create_base_query(self) -> QueryAdapter:
        """Create the base query object for this backend."""
        ...

    def apply_where(self, query: QueryAdapter, where_node: ASTNode) -> QueryAdapter:
        """Apply where conditions to the query."""
        ...

    def apply_order(self, query: QueryAdapter, order_nodes: list[OrderNode]) -> QueryAdapter:
        """Apply ordering to the query."""
        ...

    def apply_fields(self, query: QueryAdapter, fields_node: FieldsNode) -> QueryAdapter:
        """Apply field projection to the query."""
        ...

    def compile_field_condition(self, condition: FieldCondition) -> object:
        """Compile a field condition to backend-specific format."""
        ...

    def compile_logical_condition(self, condition: LogicalCondition) -> object:
        """Compile a logical condition to backend-specific format."""
        ...

    def finalize_query(self, query: QueryAdapter) -> object:
        """Finalize the query before returning (default: return as-is)."""
        ...

    def supports_backend(self, backend_type: str) -> bool:
        """Check if this compiler supports the given backend."""
        ...

    def compile_condition(self, condition: ASTNode) -> object:
        """Compile a condition node to backend-specific format."""
        ...

    def build_query(self, ast: FilterAST) -> T:
        """
        Builds a backend-specific query from a FilterAST.

        Args:
            ast: The Abstract Syntax Tree representing the filter.

        Returns:
            A backend-specific query object.
        """
        ...

    def compile(self, ast: FilterAST) -> T:
        """
        Compile FilterAST to based-specific query components.

        Args:
            ast: FilterAST to compile

        Returns:
            Dictionary with query components
        """
        ...


# Helper function for compile_condition to be used by implementations
def compile_condition_helper(compiler: BaseQueryCompiler[T], condition: ASTNode) -> object:
    """Helper function to compile a condition node to backend-specific format."""
    if isinstance(condition, FieldCondition):
        return compiler.compile_field_condition(condition)
    elif isinstance(condition, LogicalCondition):
        return compiler.compile_logical_condition(condition)
    else:
        raise CompilerError(f"Unknown condition type: {type(condition)}")
