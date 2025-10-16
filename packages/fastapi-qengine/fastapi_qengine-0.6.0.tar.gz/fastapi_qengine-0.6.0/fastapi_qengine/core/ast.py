"""
AST Builder for converting normalized filter inputs to typed AST nodes.
"""

from typing import cast

from .errors import ParseError
from .types import (
    ASTNode,
    ComparisonOperator,
    FieldCondition,
    FieldsNode,
    FilterAST,
    FilterInput,
    LogicalCondition,
    LogicalOperator,
    OrderNode,
)


class ASTBuilder:
    """Builds typed AST from normalized filter inputs."""

    def build(self, filter_input: FilterInput) -> FilterAST:
        """
        Build a FilterAST from a normalized FilterInput.

        Args:
            filter_input: Normalized FilterInput

        Returns:
            FilterAST with typed nodes
        """
        where_node = None
        order_nodes = []
        fields_node = None

        # Build where AST
        if filter_input.where is not None:
            where_node = self._build_where_node(filter_input.where)

        # Build order nodes
        if filter_input.order is not None:
            order_nodes = self._build_order_nodes(filter_input.order)

        # Build fields node
        if filter_input.fields is not None:
            fields_node = self._build_fields_node(filter_input.fields)

        return FilterAST(where=where_node, order=order_nodes, fields=fields_node)

    def _build_where_node(self, where: dict[str, object]) -> ASTNode:
        """Build where clause AST node."""
        return self._build_condition_node(where)

    def _build_condition_node(self, condition: dict[str, object]) -> ASTNode:
        """Build a condition node (field condition or logical condition)."""
        logical_operators: list[ASTNode] = []
        field_conditions: list[ASTNode] = []

        for key, value in condition.items():
            if key.startswith("$") and key in ["$and", "$or", "$nor"]:
                # Logical operator
                logical_op = LogicalOperator(key)
                if not isinstance(value, list):
                    raise ParseError(f"Logical operator '{key}' requires a list value")

                nested_conditions = [
                    self._build_condition_node(cast(dict[str, object], item)) for item in cast(list[object], value)
                ]
                logical_operators.append(LogicalCondition(operator=logical_op, conditions=nested_conditions))
            else:
                # Field condition
                field_conditions.append(self._build_field_condition(key, value))

        # Combine all conditions
        all_conditions: list[ASTNode] = logical_operators + field_conditions

        if len(all_conditions) == 1:
            return all_conditions[0]
        elif len(all_conditions) > 1:
            # Multiple conditions at same level - combine with AND
            return LogicalCondition(operator=LogicalOperator.AND, conditions=all_conditions)
        else:
            raise ParseError("Empty condition")

    def _build_field_condition(self, field: str, condition: object) -> ASTNode:
        """Build a field condition node."""
        if field.startswith("$"):
            raise ParseError(f"Invalid field name '{field}' - cannot start with '$'")

        if isinstance(condition, dict):
            return self._build_complex_field_condition(field, cast(dict[str, object], condition))
        else:
            return self._build_simple_field_condition(field, condition)

    def _build_complex_field_condition(self, field: str, condition: dict[str, object]) -> ASTNode:
        """Build a complex field condition with operators."""
        if len(condition) == 1:
            return self._build_single_operator_condition(field, condition)
        else:
            return self._build_multiple_operator_condition(field, condition)

    def _build_single_operator_condition(self, field: str, condition: dict[str, object]) -> FieldCondition:
        """Build a field condition with a single operator."""
        from typing import cast

        from .types import FilterValue

        op_key, op_value = next(iter(condition.items()))
        self._validate_operator(op_key)
        operator = self._get_comparison_operator(op_key)
        return FieldCondition(field=field, operator=operator, value=cast(FilterValue, op_value))

    def _build_multiple_operator_condition(self, field: str, condition: dict[str, object]) -> ASTNode:
        """Build a field condition with multiple operators combined with AND."""
        from typing import cast

        from .types import FilterValue

        conditions: list[ASTNode] = []
        for op_key, op_value in condition.items():
            self._validate_operator(op_key)
            operator = self._get_comparison_operator(op_key)
            conditions.append(FieldCondition(field=field, operator=operator, value=cast(FilterValue, op_value)))

        if len(conditions) == 1:
            return conditions[0]
        else:
            return LogicalCondition(operator=LogicalOperator.AND, conditions=conditions)

    def _build_simple_field_condition(self, field: str, condition: object) -> FieldCondition:
        """Build a simple equality field condition."""
        from typing import cast

        from .types import FilterValue

        return FieldCondition(
            field=field,
            operator=ComparisonOperator.EQ,
            value=cast(FilterValue, condition),
        )

    def _validate_operator(self, op_key: str) -> None:
        """Validate that an operator key is valid."""
        if not op_key.startswith("$"):
            raise ParseError(f"Invalid operator '{op_key}' - must start with '$'")

    def _get_comparison_operator(self, op_key: str) -> ComparisonOperator:
        """Get a ComparisonOperator from an operator key."""
        try:
            return ComparisonOperator(op_key)
        except ValueError:
            raise ParseError(f"Unknown operator '{op_key}'")

    def _build_order_nodes(self, order: str | list[str]) -> list[OrderNode]:
        """
        Build order nodes from order specification.

        Supports formats:
        - String: "field1 ASC,field2 DESC"
        - List of strings: ["field1 ASC", "field2 DESC"]
        - Fields with "-" prefix for descending: "-field1", "field2"
        - Fields with explicit ASC/DESC: "field1 ASC", "field2 DESC"
        """
        order_nodes: list[OrderNode] = []

        # Normalize order to list of field specs
        fields_to_process = order.split(",") if isinstance(order, str) else order

        for field_spec in fields_to_process:
            field_spec = field_spec.strip()
            if not field_spec:
                continue

            field, ascending = self._parse_field_spec(field_spec)

            if not field:
                raise ParseError("Invalid order specification - empty field name")

            order_nodes.append(OrderNode(field=field, ascending=ascending))

        return order_nodes

    def _parse_field_spec(self, field_spec: str) -> tuple[str, bool]:
        """
        Parse a field specification and return (field_name, is_ascending).

        Supports:
        - "field ASC" or "field DESC" (explicit direction)
        - "-field" (descending prefix, legacy format)
        - "field" (ascending by default)
        """
        ascending = True
        field = field_spec

        # Try explicit ASC/DESC format
        if " " in field_spec:
            parts = field_spec.rsplit(" ", 1)
            if len(parts) == 2:
                candidate_field, direction = parts
                direction = direction.strip().upper()

                if direction in ("ASC", "DESC"):
                    field = candidate_field.strip()
                    ascending = direction == "ASC"
                    return field, ascending

        # Try "-" prefix for descending (legacy format)
        if field.startswith("-"):
            ascending = False
            field = field[1:]

        return field, ascending

    def _build_fields_node(self, fields: dict[str, int]) -> FieldsNode:
        """Build fields node from fields specification."""
        # Validate field values are 0 or 1
        for field, include in fields.items():
            if include not in [0, 1]:
                raise ParseError(f"Field '{field}' inclusion value must be 0 or 1, got {include}")

        return FieldsNode(fields=fields)

    def _flatten_single_item_logical(self, node: ASTNode) -> ASTNode:
        """Flatten single-item logical conditions."""
        if isinstance(node, LogicalCondition) and len(node.conditions) == 1:
            # Single item in logical condition can be flattened
            return self._flatten_single_item_logical(node.conditions[0])
        return node


__all__ = ["ASTBuilder", "FieldCondition", "LogicalCondition"]
