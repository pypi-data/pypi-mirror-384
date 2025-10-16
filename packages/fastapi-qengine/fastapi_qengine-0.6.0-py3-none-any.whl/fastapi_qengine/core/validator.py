"""
Validator for filter inputs and AST nodes.
"""

import re
from typing import Callable, cast

from .config import ValidatorConfig
from .errors import SecurityError, ValidationError
from .types import (
    ASTNode,
    ComparisonOperator,
    FieldCondition,
    FieldsNode,
    FilterInput,
    LogicalCondition,
    OrderNode,
    OrderSpec,
    SecurityPolicy,
    ValidationRule,
)


class FilterValidator:
    """Validates filter inputs and AST nodes."""

    def __init__(
        self,
        config: ValidatorConfig | None = None,
        security_policy: SecurityPolicy | None = None,
    ):
        self.config: ValidatorConfig = config or ValidatorConfig()
        self.security_policy: SecurityPolicy = security_policy or SecurityPolicy()
        self.validation_rules: list[ValidationRule] = []
        # Operator alias maps to accept names without "$" prefix
        self._logical_aliases: dict[str, str] = {
            "$and": "$and",
            "$or": "$or",
            "$nor": "$nor",
            "and": "$and",
            "or": "$or",
            "nor": "$nor",
        }
        self._comparison_aliases: dict[str, str] = {
            "$eq": "$eq",
            "$ne": "$ne",
            "$gt": "$gt",
            "$gte": "$gte",
            "$lt": "$lt",
            "$lte": "$lte",
            "$in": "$in",
            "$nin": "$nin",
            "$regex": "$regex",
            "$exists": "$exists",
            "$size": "$size",
            "$type": "$type",
            "eq": "$eq",
            "ne": "$ne",
            "gt": "$gt",
            "gte": "$gte",
            "lt": "$lt",
            "lte": "$lte",
            "in": "$in",
            "nin": "$nin",
            "regex": "$regex",
            "exists": "$exists",
            "size": "$size",
            "type": "$type",
        }

    def add_validation_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule."""
        self.validation_rules.append(rule)

    def validate_filter_input(self, filter_input: FilterInput) -> None:
        """
        Validate a FilterInput object for security and structural correctness.
        This method performs comprehensive validation of all components within a FilterInput
        object, including where clauses, order clauses, and fields clauses. It prioritizes
        security violations over general validation errors.
        Args:
            filter_input (FilterInput): The filter input object to validate containing
                optional where, order, and fields clauses.
        Raises:
            SecurityError: If any security policy violations are detected in any clause.
                This exception takes priority over ValidationError and includes all
                security issues found across all clauses.
            ValidationError: If structural or syntax validation fails for any clause.
                Only raised if no security errors are present.
        Note:
            - Security errors are collected and raised together with priority over
              validation errors
            - All clauses are validated even if earlier ones fail, to provide
              comprehensive error reporting
            - None values for optional clauses (where, order, fields) are safely ignored
        """
        errors: list[str] = []
        security_errors: list[str] = []

        self._validate_all_clauses(filter_input, errors, security_errors)
        self._raise_collected_errors(errors, security_errors)

    def _validate_all_clauses(
        self, filter_input: FilterInput, errors: list[str], security_errors: list[str]
    ) -> None:
        """Validate all clauses in the filter input and collect errors."""
        if filter_input.where is not None:
            try:
                self._validate_where_clause(filter_input.where)
            except SecurityError as e:
                security_errors.append(str(e))
            except ValidationError as e:
                errors.append(str(e))
        if filter_input.order is not None:
            try:
                self._validate_order_clause(filter_input.order)
            except SecurityError as e:
                security_errors.append(str(e))
            except ValidationError as e:
                errors.append(str(e))
        if filter_input.fields is not None:
            try:
                self._validate_fields_clause(filter_input.fields)
            except SecurityError as e:
                security_errors.append(str(e))
            except ValidationError as e:
                errors.append(str(e))

    def _validate_clause(
        self,
        clause_value: object,
        validation_method: Callable[[object], None],
        errors: list[str],
        security_errors: list[str],
    ) -> None:
        """Validate a single clause and collect any errors."""
        if clause_value is not None:
            try:
                validation_method(clause_value)
            except SecurityError as e:
                security_errors.append(str(e))
            except ValidationError as e:
                errors.append(str(e))

    def _raise_collected_errors(
        self, errors: list[str], security_errors: list[str]
    ) -> None:
        """Raise collected errors, prioritizing security errors."""
        if security_errors:
            raise SecurityError(
                f"Security policy violation: {'; '.join(security_errors)}"
            )
        if errors:
            raise ValidationError(f"Filter validation failed: {'; '.join(errors)}")

    def validate_ast_node(self, node: ASTNode) -> list[str]:
        """Validate an AST node and return list of error messages."""
        errors: list[str] = []

        # Built-in validations
        if isinstance(node, FieldCondition):
            errors.extend(self._validate_field_condition(node))
        elif isinstance(node, LogicalCondition):
            errors.extend(self._validate_logical_condition(node))
        elif isinstance(node, OrderNode):
            errors.extend(self._validate_order_node(node))
        elif isinstance(node, FieldsNode):
            errors.extend(self._validate_fields_node(node))

        # Apply custom validation rules
        for rule in self.validation_rules:
            errors.extend(rule.validate(node))

        return errors

    def _validate_where_clause(self, where: dict[str, object], depth: int = 0) -> None:
        """Validate where clause structure and security."""
        # Check depth limit
        if depth > self.security_policy.max_depth:
            raise SecurityError(
                f"Query depth exceeds maximum of {self.security_policy.max_depth}"
            )

        for key, value in where.items():
            if self._canonical_operator(key).startswith("$"):
                # Logical or comparison operator
                self._validate_operator(key, value, depth)
            else:
                # Field name
                self._validate_field_access(key)
                self._validate_field_condition_value(value, depth)

    def _validate_operator(self, operator: str, value: object, depth: int) -> None:
        """Validate operator usage."""
        # Canonicalize to "$" form if an alias without prefix is used
        operator = self._canonical_operator(operator)
        # Check if operator is allowed
        if self.security_policy.allowed_operators is not None:
            operator_enum = self._get_operator_enum(operator)
            if (
                operator_enum
                and operator_enum not in self.security_policy.allowed_operators
            ):
                raise SecurityError(f"Operator '{operator}' is not allowed")

        # Validate operator-specific rules
        if operator in ["$and", "$or", "$nor"]:
            self._validate_logical_operator(
                operator, cast(list[dict[str, object]], value), depth
            )
        elif operator in ["$in", "$nin"]:
            self._validate_array_operator(operator, value)
        elif operator in ["$regex"]:
            self._validate_regex_operator(operator, value)
        elif operator in ["$exists"]:
            self._validate_exists_operator(operator, value)
        elif operator in ["$size"]:
            self._validate_size_operator(operator, value)
        # Add more operator-specific validations as needed

    def _validate_logical_operator(
        self, operator: str, value: list[dict[str, object]], depth: int
    ) -> None:
        """Validate logical operator values."""
        if len(value) == 0:
            raise ValidationError(f"Operator '{operator}' cannot have empty array")

        # Recursively validate nested conditions
        for item in value:
            self._validate_where_clause(item, depth + 1)

    def _validate_array_operator(self, operator: str, value: object) -> None:
        """Validate array operators like $in, $nin."""
        if not isinstance(value, list):
            raise ValidationError(f"Operator '{operator}' requires an array value")

        value_list = cast(list[object], value)
        if len(value_list) > self.security_policy.max_array_size:
            raise SecurityError(
                f"Array size exceeds maximum of {self.security_policy.max_array_size}"
            )

    def _validate_regex_operator(self, operator: str, value: object) -> None:
        """Validate regex operator."""
        if not isinstance(value, str):
            raise ValidationError(f"Operator '{operator}' requires a string value")

        # Try to compile regex to check for validity
        try:
            _ = re.compile(value)
        except re.error as e:
            raise ValidationError(f"Invalid regex pattern: {e}")

    def _validate_exists_operator(self, operator: str, value: object) -> None:
        """Validate exists operator."""
        if not isinstance(value, bool):
            raise ValidationError(f"Operator '{operator}' requires a boolean value")

    def _validate_size_operator(self, operator: str, value: object) -> None:
        """Validate size operator."""
        if not isinstance(value, int) or value < 0:
            raise ValidationError(
                f"Operator '{operator}' requires a non-negative integer"
            )

    def _validate_field_access(self, field_name: str) -> None:
        """Validate field access according to security policy."""
        # Check blocked fields
        if (
            self.security_policy.blocked_fields
            and field_name in self.security_policy.blocked_fields
        ):
            raise SecurityError(f"Access to field '{field_name}' is blocked")

        # Check allowed fields (if whitelist is defined)
        if (
            self.security_policy.allowed_fields
            and field_name not in self.security_policy.allowed_fields
        ):
            raise SecurityError(f"Access to field '{field_name}' is not allowed")

        # Basic field name validation
        if not field_name:
            raise ValidationError("Field names must be non-empty strings")

    def _validate_field_condition_value(self, value: object, depth: int) -> None:
        """Validate field condition value."""
        if isinstance(value, dict):
            # Complex condition with operators
            value_dict = cast(dict[str, object], value)
            for op, op_value in value_dict.items():
                self._validate_operator(op, op_value, depth)
        # Simple value conditions are generally allowed

    def _validate_order_clause(self, order: OrderSpec) -> None:
        """Validate order clause."""
        # Parse order fields
        if isinstance(order, str):
            field_specs = order.split(",")
        else:
            field_specs = order
        for field_spec in field_specs:
            field_spec = field_spec.strip()
            if not field_spec:
                continue

            # Extract field name (remove - prefix for descending)
            field_name = field_spec.lstrip("-")
            self._validate_field_access(field_name)

    def _validate_fields_clause(self, fields: dict[str, int]) -> None:
        """Validate fields clause."""

        for field_name, include in fields.items():
            self._validate_field_access(field_name)
            if include not in [0, 1]:
                raise ValidationError(
                    f"Field inclusion value must be 0 or 1, got {include}"
                )

    def _validate_field_condition(self, node: FieldCondition) -> list[str]:
        """Validate a field condition node."""
        errors: list[str] = []

        try:
            self._validate_field_access(node.field)
        except (ValidationError, SecurityError) as e:
            errors.append(str(e))

        return errors

    def _validate_logical_condition(self, node: LogicalCondition) -> list[str]:
        """Validate a logical condition node."""
        errors: list[str] = []

        if not node.conditions:
            errors.append(
                f"Logical operator '{node.operator.value}' cannot have empty conditions"
            )

        # Recursively validate nested conditions
        for condition in node.conditions:
            errors.extend(self.validate_ast_node(condition))

        return errors

    def _validate_order_node(self, node: OrderNode) -> list[str]:
        """Validate an order node."""
        errors: list[str] = []

        try:
            self._validate_field_access(node.field)
        except (ValidationError, SecurityError) as e:
            errors.append(str(e))

        return errors

    def _validate_fields_node(self, node: FieldsNode) -> list[str]:
        """Validate a fields node."""
        errors: list[str] = []

        for field_name in node.fields.keys():
            try:
                self._validate_field_access(field_name)
            except (ValidationError, SecurityError) as e:
                errors.append(str(e))

        return errors

    def _get_operator_enum(self, operator: str) -> ComparisonOperator | None:
        """Get ComparisonOperator enum for string operator."""
        try:
            return ComparisonOperator(self._canonical_operator(operator))
        except ValueError:
            return None

    def _canonical_operator(self, operator: str) -> str:
        """Map operator aliases to canonical "$"-prefixed form when possible."""
        op_lower = operator.lower()
        if op_lower in self._logical_aliases:
            return self._logical_aliases[op_lower]
        if op_lower in self._comparison_aliases:
            return self._comparison_aliases[op_lower]
        # If already starts with "$", keep as is
        return operator
