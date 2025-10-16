"""
Type definitions for fastapi-qengine.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeAlias, TypeVar

# Basic type aliases
FilterValue: TypeAlias = str | int | float | bool | list[object] | dict[str, object]
FilterDict: TypeAlias = dict[str, object]
OrderSpec: TypeAlias = str | list[str]
FieldsSpec: TypeAlias = dict[str, int]


T = TypeVar("T", covariant=True)


class FilterFormat(Enum):
    """Supported filter input formats."""

    NESTED_PARAMS = "nested_params"
    JSON_STRING = "json_string"
    DICT_OBJECT = "dict_object"


class LogicalOperator(Enum):
    """Logical operators for combining conditions."""

    AND = "$and"
    OR = "$or"
    NOR = "$nor"


class ComparisonOperator(Enum):
    """Comparison operators for field conditions."""

    EQ = "$eq"  # Equal
    NE = "$ne"  # Not equal
    GT = "$gt"  # Greater than
    GTE = "$gte"  # Greater than or equal
    LT = "$lt"  # Less than
    LTE = "$lte"  # Less than or equal
    IN = "$in"  # In array
    NIN = "$nin"  # Not in array
    REGEX = "$regex"  # Regular expression
    EXISTS = "$exists"  # Field exists
    SIZE = "$size"  # Array size
    TYPE = "$type"  # Field type


@dataclass
class FilterInput:
    """Raw filter input from the request."""

    where: FilterDict | None = None
    order: OrderSpec | None = None
    fields: FieldsSpec | None = None
    format: FilterFormat = FilterFormat.DICT_OBJECT


@dataclass
class ASTNode:
    """Base class for AST nodes."""

    pass


@dataclass
class FieldCondition(ASTNode):
    """A condition on a specific field."""

    field: str
    operator: ComparisonOperator
    value: FilterValue


@dataclass
class LogicalCondition(ASTNode):
    """A logical combination of conditions."""

    operator: LogicalOperator
    conditions: list[ASTNode]


@dataclass
class OrderNode(ASTNode):
    """Represents ordering specification."""

    field: str
    ascending: bool = True


@dataclass
class FieldsNode(ASTNode):
    """Represents field projection."""

    fields: dict[str, int]


@dataclass
class FilterAST:
    """Complete filter Abstract Syntax Tree."""

    where: ASTNode | None = None
    order: list[OrderNode] | None = None
    fields: FieldsNode | None = None

    def __post_init__(self):
        if self.order is None:
            self.order = []


class BackendQuery(Protocol):
    """Protocol for backend-specific query objects."""

    def apply_where(self, condition: ASTNode) -> "BackendQuery":
        """Apply where conditions to the query."""
        ...

    def apply_order(self, order_nodes: list[OrderNode]) -> "BackendQuery":
        """Apply ordering to the query."""
        ...

    def apply_fields(self, fields_node: FieldsNode) -> "BackendQuery":
        """Apply field projection to the query."""
        ...


class ValidationRule(Protocol):
    """Protocol for validation rules."""

    def validate(self, node: ASTNode) -> list[str]:
        """Validate a node and return list of error messages."""
        ...


@dataclass
class SecurityPolicy:
    """Security policy for query execution."""

    max_depth: int = 10
    allowed_operators: list[ComparisonOperator] | None = None
    allowed_fields: list[str] | None = None
    blocked_fields: list[str] | None = None
    max_array_size: int = 1000


class Engine(Protocol[T]):
    """
    Protocol to standardize query engines for different database backends.

    This protocol defines a common interface for all query engines, ensuring that
    they can be used interchangeably within the system.
    """
