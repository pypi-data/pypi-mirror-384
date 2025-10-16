"""
AST Optimizer for simplifying and optimizing filter ASTs.
"""

from .config import OptimizerConfig
from .types import (
    ASTNode,
    FieldCondition,
    FilterAST,
    LogicalCondition,
    LogicalOperator,
    OrderNode,
)


class ASTOptimizer:
    """Optimizes filter ASTs for better performance."""

    def __init__(self, config: OptimizerConfig | None = None):
        self.config: OptimizerConfig = config or OptimizerConfig()

    def optimize(self, ast: FilterAST) -> FilterAST:
        """
        Optimize a FilterAST.

        Args:
            ast: Input FilterAST

        Returns:
            Optimized FilterAST
        """
        if not self.config.enabled:
            return ast

        optimized_ast = FilterAST(
            where=ast.where,
            order=ast.order[:] if ast.order else [],  # Copy order nodes
            fields=ast.fields,
        )

        # Optimize where clause
        if optimized_ast.where is not None:
            for _ in range(self.config.max_optimization_passes):
                original = optimized_ast.where
                if optimized_ast.where is not None:
                    optimized_ast.where = self._optimize_node(optimized_ast.where)

                # Stop if no changes were made
                if self._nodes_equal(original, optimized_ast.where):
                    break

        # Optimize order (remove duplicates, etc.)
        if optimized_ast.order:
            optimized_ast.order = self._optimize_order_nodes(optimized_ast.order)

        return optimized_ast

    def _optimize_node(self, node: ASTNode) -> ASTNode | None:
        """Optimize a single AST node."""
        if isinstance(node, LogicalCondition):
            return self._optimize_logical_condition(node)
        elif isinstance(node, FieldCondition):
            return self._optimize_field_condition(node)
        else:
            return node

    def _optimize_logical_condition(
        self, condition: LogicalCondition
    ) -> ASTNode | None:
        """Optimize a logical condition node."""
        # First, optimize all child conditions
        optimized_conditions: list[ASTNode] = []
        for child in condition.conditions:
            optimized_child = self._optimize_node(child)
            if optimized_child is not None:
                optimized_conditions.append(optimized_child)

        # If no children remain after optimization, return None
        if not optimized_conditions:
            return None

        # If only one child remains, return it directly (flattening)
        if len(optimized_conditions) == 1:
            return optimized_conditions[0]

        # Apply range condition optimization if enabled
        if self.config.combine_range_conditions:
            optimized_conditions = self._combine_range_conditions(optimized_conditions)

        # Simplify nested logical operators of the same type
        flattened_conditions: list[ASTNode] = []
        for child in optimized_conditions:
            if (
                isinstance(child, LogicalCondition)
                and child.operator == condition.operator
            ):
                # Flatten nested AND/OR with same operator
                flattened_conditions.extend(child.conditions)
            else:
                flattened_conditions.append(child)

        # Remove redundant conditions if enabled
        if self.config.remove_redundant_conditions:
            flattened_conditions = self._remove_redundant_conditions(
                flattened_conditions
            )

        # If we've reduced to a single condition through flattening, return it
        if len(flattened_conditions) == 1:
            return flattened_conditions[0]

        # Otherwise return the optimized logical condition
        return LogicalCondition(
            operator=condition.operator, conditions=flattened_conditions
        )

    def _optimize_field_condition(self, node: FieldCondition) -> FieldCondition:
        """Optimize a field condition node."""
        # For now, just return as-is
        # Future optimizations could include:
        # - Converting ranges to more efficient operators
        # - Normalizing values
        return node

    def _simplify_logical_operators(
        self, operator: LogicalOperator, conditions: list[ASTNode]
    ) -> list[ASTNode]:
        """Simplify nested logical operators of the same type."""
        simplified: list[ASTNode] = []

        for condition in conditions:
            if (
                isinstance(condition, LogicalCondition)
                and condition.operator == operator
            ):
                # Flatten nested logical operators of same type
                # $and: [$and: [a, b], c] -> $and: [a, b, c]
                simplified.extend(condition.conditions)
            else:
                simplified.append(condition)

        return simplified

    def _combine_range_conditions(self, conditions: list[ASTNode]) -> list[ASTNode]:
        """Combine range conditions on the same field."""
        if not self.config.combine_range_conditions:
            return conditions

        # Group field conditions by field name
        field_conditions: dict[str, list[FieldCondition]] = {}
        other_conditions: list[ASTNode] = []

        for condition in conditions:
            if isinstance(condition, FieldCondition):
                if condition.field not in field_conditions:
                    field_conditions[condition.field] = []
                field_conditions[condition.field].append(condition)
            else:
                other_conditions.append(condition)

        # Combine range conditions for each field
        combined_conditions: list[ASTNode] = []
        for field_conds in field_conditions.values():
            if len(field_conds) == 1:
                combined_conditions.append(field_conds[0])
            else:
                # Try to combine range conditions
                combined = self._try_combine_field_conditions(field_conds)
                combined_conditions.extend(combined)

        return combined_conditions + other_conditions

    def _try_combine_field_conditions(
        self, conditions: list[FieldCondition]
    ) -> list[FieldCondition]:
        """Try to combine multiple conditions on the same field."""
        # For now, just return as-is
        # Future optimization could combine things like:
        # price >= 10 AND price <= 100 -> price: {$gte: 10, $lte: 100}
        return conditions

    def _remove_redundant_conditions(self, conditions: list[ASTNode]) -> list[ASTNode]:
        """Remove redundant conditions."""
        if not self.config.remove_redundant_conditions:
            return conditions

        # Remove exact duplicates
        seen: set[str] = set()
        unique_conditions: list[ASTNode] = []

        for condition in conditions:
            condition_key = self._get_condition_key(condition)
            if condition_key not in seen:
                seen.add(condition_key)
                unique_conditions.append(condition)

        return unique_conditions

    def _get_condition_key(self, condition: ASTNode) -> str:
        """Get a string key for a condition for deduplication."""
        if isinstance(condition, FieldCondition):
            return (
                f"field:{condition.field}:{condition.operator.value}:{condition.value}"
            )
        elif isinstance(condition, LogicalCondition):
            sub_keys = [self._get_condition_key(c) for c in condition.conditions]
            return f"logical:{condition.operator.value}:{','.join(sorted(sub_keys))}"
        else:
            return str(condition)

    def _optimize_order_nodes(self, order_nodes: list[OrderNode]) -> list[OrderNode]:
        """Optimize order nodes."""
        if not order_nodes:
            return []

        # Remove duplicate order fields (keep first occurrence)
        seen_fields: set[str] = set()
        unique_order: list[OrderNode] = []

        for order_node in order_nodes:
            if order_node.field not in seen_fields:
                seen_fields.add(order_node.field)
                unique_order.append(order_node)

        return unique_order

    def _nodes_equal(self, node1: ASTNode | None, node2: ASTNode | None) -> bool:
        """Check if two nodes are equal."""
        if node1 is None and node2 is None:
            return True
        if node1 is None or node2 is None:
            return False

        if not isinstance(node1, type(node2)):
            return False

        if isinstance(node1, FieldCondition) and isinstance(node2, FieldCondition):
            return self._field_conditions_equal(node1, node2)

        elif isinstance(node1, LogicalCondition) and isinstance(
            node2, LogicalCondition
        ):
            return self._logical_conditions_equal(node1, node2)

        return False

    def _field_conditions_equal(
        self, node1: FieldCondition, node2: FieldCondition
    ) -> bool:
        """Check if two field conditions are equal."""
        return (
            node1.field == node2.field
            and node1.operator == node2.operator
            and node1.value == node2.value
        )

    def _logical_conditions_equal(
        self, node1: LogicalCondition, node2: LogicalCondition
    ) -> bool:
        """Check if two logical conditions are equal."""
        if node1.operator != node2.operator:
            return False
        if len(node1.conditions) != len(node2.conditions):
            return False

        # Check if all conditions are equal (order-independent for commutative operators)
        if node1.operator in [LogicalOperator.AND, LogicalOperator.OR]:
            return self._commutative_conditions_equal(
                node1.conditions, node2.conditions
            )
        else:
            return self._ordered_conditions_equal(node1.conditions, node2.conditions)

    def _commutative_conditions_equal(
        self, conditions1: list[ASTNode], conditions2: list[ASTNode]
    ) -> bool:
        """Check if two lists of conditions are equal for commutative operators."""
        keys1 = [self._get_condition_key(c) for c in conditions1]
        keys2 = [self._get_condition_key(c) for c in conditions2]
        return sorted(keys1) == sorted(keys2)

    def _ordered_conditions_equal(
        self, conditions1: list[ASTNode], conditions2: list[ASTNode]
    ) -> bool:
        """Check if two lists of conditions are equal in order."""
        return all(
            self._nodes_equal(c1, c2) for c1, c2 in zip(conditions1, conditions2)
        )
