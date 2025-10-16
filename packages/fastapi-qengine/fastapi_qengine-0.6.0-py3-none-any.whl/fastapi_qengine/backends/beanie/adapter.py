"""
Beanie query adapter.

This module contains the BeanieQueryAdapter class for building Beanie/PyMongo queries.
"""

from typing import Literal, cast

from fastapi_qengine.core.compiler_base import QueryAdapter


class BeanieQueryAdapter:
    """Adapter for Beanie/PyMongo query objects."""

    def __init__(self) -> None:
        self.query: dict[str, object] = {}
        self.sort_spec: list[tuple[str, int]] = []
        self.projection: dict[str, int] | None = None

    def add_where_condition(self, condition: object) -> "QueryAdapter":
        """Add a where condition to the query."""
        condition_dict = cast(dict[str, object], condition)
        if not self.query:
            self.query = condition_dict
        else:
            # Merge with existing query using $and
            if "$and" in self.query:
                cast(list[object], self.query["$and"]).append(condition_dict)
            else:
                self.query = {"$and": [self.query, condition_dict]}
        return self

    def add_sort(self, field: str, ascending: bool = True) -> "QueryAdapter":
        """Add sorting to the query."""
        direction: Literal[1, -1] = 1 if ascending else -1
        self.sort_spec.append((field, direction))
        return self

    def set_projection(self, fields: dict[str, int]) -> "QueryAdapter":
        """Set field projection."""
        self.projection = fields
        return self

    def build(self) -> dict[str, object]:
        """Build the final query components."""
        result: dict[str, object] = {}

        if self.query:
            result["filter"] = self.query

        if self.sort_spec:
            result["sort"] = self.sort_spec

        if self.projection:
            result["projection"] = self.projection

        return result
