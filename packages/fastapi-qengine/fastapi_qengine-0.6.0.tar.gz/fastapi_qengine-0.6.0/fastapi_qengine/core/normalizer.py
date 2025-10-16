"""
Normalizer for filter inputs to canonical format.

Enhancement: Accept operator aliases without MongoDB's "$" prefix.
This keeps the public/global operator names neutral (e.g., eq, gt, in)
while still normalizing to the canonical internal representation expected
by the AST builder and backends. Logical operators (and, or, nor) and
comparison operators (eq, ne, gt, gte, lt, lte, in, nin, regex, exists,
size, type) are supported with or without the "$" prefix.
"""

from typing import cast

from .errors import ValidationError
from .types import FieldsSpec, FilterDict, FilterInput, OrderSpec


class FilterNormalizer:
    """Normalizes filter inputs to a canonical format."""

    # Mapping of logical operator aliases to canonical "$" form
    _LOGICAL_ALIASES: dict[str, str] = {
        "$and": "$and",
        "$or": "$or",
        "$nor": "$nor",
        # alias without prefix
        "and": "$and",
        "or": "$or",
        "nor": "$nor",
    }

    # Mapping of comparison operator aliases to canonical "$" form
    _COMPARISON_ALIASES: dict[str, str] = {
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
        # aliases without prefix
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

    @classmethod
    def _canon_logical(cls, key: str) -> str:
        """Return canonical logical operator (with "$"), or original if unknown."""
        return cls._LOGICAL_ALIASES.get(key, cls._LOGICAL_ALIASES.get(key.lower(), key))

    @classmethod
    def _canon_comparison(cls, key: str) -> str:
        """Return canonical comparison operator (with "$"), or original if unknown."""
        return cls._COMPARISON_ALIASES.get(key, cls._COMPARISON_ALIASES.get(key.lower(), key))

    def normalize(self, filter_input: FilterInput) -> FilterInput:
        """
        Normalize a FilterInput to canonical format.

        Args:
            filter_input: Raw FilterInput from parser

        Returns:
            Normalized FilterInput with canonical structure
        """
        normalized_where = None
        normalized_order = None
        normalized_fields = None

        # Normalize where clause
        if filter_input.where is not None:
            normalized_where = self._normalize_where(filter_input.where)

        # Normalize order clause
        if filter_input.order is not None:
            normalized_order = self._normalize_order(filter_input.order)

        # Normalize fields clause
        if filter_input.fields is not None:
            normalized_fields = self._normalize_fields(filter_input.fields)

        return FilterInput(
            where=normalized_where,
            order=normalized_order,
            fields=normalized_fields,
            format=filter_input.format,
        )

    def _normalize_where(self, where: FilterDict) -> FilterDict:
        """Normalize where conditions to canonical format."""
        return cast(FilterDict, self._normalize_condition(where))

    def _normalize_condition(self, condition: object) -> object:
        """Recursively normalize a condition."""
        if not isinstance(condition, dict):
            return condition

        condition_dict = cast(dict[str, object], condition)
        normalized: dict[str, object] = {}

        for key, value in condition_dict.items():
            # Handle logical operators with or without "$" prefix
            logical_key = self._canon_logical(key)
            if logical_key in ["$and", "$or", "$nor"]:
                normalized[logical_key] = self._normalize_operator_value(logical_key, value)
            else:
                # Field condition
                normalized[key] = self._normalize_field_condition(value)

        return normalized

    def _normalize_operator_value(self, operator: str, value: object) -> object:
        """Normalize operator value."""
        if operator in ["$and", "$or", "$nor"]:
            # Logical operators expect arrays
            if not isinstance(value, list):
                raise ValidationError(f"Operator '{operator}' requires an array value")
            normalized_list = cast(list[object], value)
            return [self._normalize_condition(item) for item in normalized_list]
        else:
            # Comparison operators
            return value

    def _normalize_field_condition(self, condition: object) -> object:
        """Normalize a field condition."""
        if not isinstance(condition, dict):
            # Simple equality: field: value -> field: {$eq: value}
            return {"$eq": condition}

        # Complex condition with operators
        normalized: dict[str, object] = {}
        for op, value in cast(dict[str, object], condition).items():
            canon = self._canon_comparison(op)
            # If after canonicalization it's still not a known "$" operator, reject
            if not canon.startswith("$"):
                raise ValidationError(f"Invalid operator '{op}'. Use standard names (eq, gt, in, ...) or '$' prefixed")
            normalized[canon] = value

        return normalized

    def _normalize_order(self, order: OrderSpec) -> str:
        """
        Normalize order specification to a string format.

        Handles the following formats:
        1. String: "propertyName ASC" or "propertyName DESC"
        2. Array: ["propertyName1 ASC", "propertyName2 DESC"]
        3. dictionary with numeric indices: {0: "propertyName1 ASC", 1: "propertyName2 DESC"}

        Returns a comma-separated string format that the AST builder can process.
        """
        if isinstance(order, dict):
            return self._normalize_order_dict(order)
        elif isinstance(order, list):
            return self._normalize_order_list(order)
        else:
            return order.strip()

    def _normalize_order_list(self, order_list: list[str]) -> str:
        """Normalize a list of order specifications."""
        order_items: list[str] = []
        for item in order_list:
            order_items.append(item.strip())
        return ",".join(order_items)

    def _normalize_order_dict(self, order_dict: dict[str, str | int]) -> str:
        """Normalize a dictionary of order specifications."""
        try:
            return self._normalize_numeric_key_dict(order_dict)
        except (ValueError, TypeError):
            return self._normalize_non_numeric_dict(order_dict)

    def _normalize_numeric_key_dict(self, order_dict: dict[str, str | int]) -> str:
        """Process dictionary with numeric keys."""
        # Try to convert keys to integers and sort
        sorted_keys = sorted([int(k) for k in order_dict.keys()])
        order_items: list[str] = []
        for key in sorted_keys:
            actual_key = str(key)
            value = order_dict[actual_key]
            if not isinstance(value, str):
                raise ValidationError(f"Order item must be a string, got {type(value)}")
            order_items.append(value.strip())
        return ",".join(order_items)

    def _normalize_non_numeric_dict(self, order_dict: dict[str, str | int]) -> str:
        """Process dictionary with non-numeric keys."""
        order_items: list[str] = []
        for item in order_dict.values():
            if not isinstance(item, str):
                raise ValidationError(f"Order item must be a string, got {type(item)}")
            order_items.append(item.strip())
        return ",".join(order_items)

    def _normalize_fields(self, fields: FieldsSpec) -> dict[str, int]:
        """Normalize fields specification."""
        normalized: dict[str, int] = {}
        for field, include in fields.items():
            # Normalize include value to 0 or 1
            if isinstance(include, bool):
                normalized[field] = 1 if include else 0
            elif isinstance(include, (int, float)):
                normalized[field] = int(include)
            else:
                raise ValidationError(f"Field inclusion value must be boolean or number, got {type(include)}")

        return normalized

    def _simplify_logical_operators(self, condition: dict[str, object]) -> dict[str, object]:
        """Simplify redundant logical operators."""
        simplified: dict[str, object] = {}

        for key, value in condition.items():
            if key in ["$and", "$or"]:
                simplified.update(self._process_logical_operator(key, value))
            else:
                simplified[key] = self._process_regular_field(value)

        return simplified

    def _process_logical_operator(self, operator: str, value: object) -> dict[str, object]:
        """Process logical operators ($and, $or) and simplify them."""
        if not isinstance(value, list):
            return {operator: value}

        simplified_items = [
            self._simplify_logical_operators(cast(dict[str, object], item)) for item in cast(list[object], value)
        ]
        return self._handle_simplified_logical_items(operator, cast(list[object], simplified_items))

    def _handle_simplified_logical_items(self, operator: str, items: list[object]) -> dict[str, object]:
        """Handle simplified logical operator items."""
        if len(items) == 1:
            return self._merge_single_logical_item(items[0])
        return {operator: items}

    def _merge_single_logical_item(self, item: object) -> dict[str, object]:
        """Merge single logical operator item into parent."""
        if isinstance(item, dict):
            return cast(dict[str, object], item)
        return {}

    def _process_regular_field(self, value: object) -> object:
        """Process regular field values."""
        if isinstance(value, dict):
            return self._simplify_logical_operators(cast(dict[str, object], value))
        return value
