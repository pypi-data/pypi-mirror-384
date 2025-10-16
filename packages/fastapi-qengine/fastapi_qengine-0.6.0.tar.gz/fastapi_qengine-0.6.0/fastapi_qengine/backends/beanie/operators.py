"""
Beanie backend operator registrations.

This module registers compilation functions for operators specific to the Beanie/PyMongo backend.
"""

from ...operators.base.registry import global_operator_registry


def _register_beanie_comparison_operators():
    """Register comparison operators for Beanie backend."""

    def compile_eq(field: str, value: object) -> dict[str, object]:
        """Compile $eq operator for Beanie."""
        return {field: value}

    def compile_ne(field: str, value: object) -> dict[str, object]:
        """Compile $ne operator for Beanie."""
        return {field: {"$ne": value}}

    def compile_gt(field: str, value: object) -> dict[str, object]:
        """Compile $gt operator for Beanie."""
        return {field: {"$gt": value}}

    def compile_gte(field: str, value: object) -> dict[str, object]:
        """Compile $gte operator for Beanie."""
        return {field: {"$gte": value}}

    def compile_lt(field: str, value: object) -> dict[str, object]:
        """Compile $lt operator for Beanie."""
        return {field: {"$lt": value}}

    def compile_lte(field: str, value: object) -> dict[str, object]:
        """Compile $lte operator for Beanie."""
        return {field: {"$lte": value}}

    def compile_in(field: str, value: object) -> dict[str, object]:
        """Compile $in operator for Beanie."""
        return {field: {"$in": value}}

    def compile_nin(field: str, value: object) -> dict[str, object]:
        """Compile $nin operator for Beanie."""
        return {field: {"$nin": value}}

    def compile_regex(field: str, value: object) -> dict[str, object]:
        """Compile $regex operator for Beanie."""
        return {field: {"$regex": value}}

    def compile_exists(field: str, value: object) -> dict[str, object]:
        """Compile $exists operator for Beanie."""
        return {field: {"$exists": value}}

    def compile_size(field: str, value: object) -> dict[str, object]:
        """Compile $size operator for Beanie."""
        return {field: {"$size": value}}

    def compile_type(field: str, value: object) -> dict[str, object]:
        """Compile $type operator for Beanie."""
        return {field: {"$type": value}}

    # Register all comparison operators
    global_operator_registry.register_compiler("$eq", "beanie", compile_eq)
    global_operator_registry.register_compiler("$ne", "beanie", compile_ne)
    global_operator_registry.register_compiler("$gt", "beanie", compile_gt)
    global_operator_registry.register_compiler("$gte", "beanie", compile_gte)
    global_operator_registry.register_compiler("$lt", "beanie", compile_lt)
    global_operator_registry.register_compiler("$lte", "beanie", compile_lte)
    global_operator_registry.register_compiler("$in", "beanie", compile_in)
    global_operator_registry.register_compiler("$nin", "beanie", compile_nin)
    global_operator_registry.register_compiler("$regex", "beanie", compile_regex)
    global_operator_registry.register_compiler("$exists", "beanie", compile_exists)
    global_operator_registry.register_compiler("$size", "beanie", compile_size)
    global_operator_registry.register_compiler("$type", "beanie", compile_type)


def _register_beanie_logical_operators():
    """Register logical operators for Beanie backend."""

    def compile_and(conditions: list[object]) -> dict[str, list[object]]:
        """Compile $and operator for Beanie."""
        return {"$and": conditions}

    def compile_or(conditions: list[object]) -> dict[str, list[object]]:
        """Compile $or operator for Beanie."""
        return {"$or": conditions}

    def compile_nor(conditions: list[object]) -> dict[str, list[object]]:
        """Compile $nor operator for Beanie."""
        return {"$nor": conditions}

    # Register logical operators
    global_operator_registry.register_compiler("$and", "beanie", compile_and)
    global_operator_registry.register_compiler("$or", "beanie", compile_or)
    global_operator_registry.register_compiler("$nor", "beanie", compile_nor)


def _register_beanie_custom_operators():
    """Register custom operators for Beanie backend."""

    def compile_text(field: str, value: object) -> dict[str, object]:
        """Compile $text operator for Beanie."""
        _ = field
        return {"$text": {"$search": value}}

    def compile_geo_within(field: str, value: object) -> dict[str, object]:
        """Compile $geoWithin operator for Beanie."""
        return {field: {"$geoWithin": value}}

    def compile_near(field: str, value: object) -> dict[str, object]:
        """Compile $near operator for Beanie."""
        return {field: {"$near": value}}

    # Register custom operators
    global_operator_registry.register_compiler("$text", "beanie", compile_text)
    global_operator_registry.register_compiler(
        "$geoWithin", "beanie", compile_geo_within
    )
    global_operator_registry.register_compiler("$near", "beanie", compile_near)


def register_beanie_operators():
    """Register all Beanie backend operators."""
    _register_beanie_comparison_operators()
    _register_beanie_logical_operators()
    _register_beanie_custom_operators()


# Register operators when module is imported
register_beanie_operators()
