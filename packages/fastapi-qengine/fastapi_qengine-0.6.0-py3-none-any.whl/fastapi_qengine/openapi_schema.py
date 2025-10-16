"""
OpenAPI schema generation for query filters.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Union, cast, get_args, get_origin, get_type_hints

from pydantic import BaseModel


class FilterSchemaGenerator:
    """
    Generates OpenAPI schemas for filter parameters based on model classes.
    """

    TYPE_MAPPING: dict[object, object] = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        datetime: {"type": "string", "format": "date-time"},
        date: {"type": "string", "format": "date"},
        Decimal: {"type": "number"},
    }

    OPERATORS: dict[str, str] = {
        "$eq": "Equal to",
        "$ne": "Not equal to",
        "$gt": "Greater than",
        "$gte": "Greater than or equal to",
        "$lt": "Less than",
        "$lte": "Less than or equal to",
        "$in": "Value in array",
        "$nin": "Value not in array",
        "$regex": "Regular expression match",
        "$exists": "Field exists",
        "$and": "Logical AND",
        "$or": "Logical OR",
        "$not": "Logical NOT",
    }

    def __init__(self, model_class: type[BaseModel]):
        self.model_class: type[BaseModel] = model_class
        self.model_fields: dict[str, dict[str, object]] = self._get_model_fields()

    def _get_model_fields(self) -> dict[str, dict[str, object]]:
        """Extract field information from model."""
        if hasattr(self.model_class, "model_fields"):
            return self._extract_pydantic_v2_fields()
        else:
            return self._extract_fallback_fields()

    def _extract_pydantic_v2_fields(self) -> dict[str, dict[str, object]]:
        """Extract fields from Pydantic v2 model."""
        fields: dict[str, dict[str, object]] = {}
        for field_name, field_info in self.model_class.model_fields.items():
            fields[field_name] = {
                "type": field_info.annotation,
                "required": field_info.is_required(),
                "description": getattr(field_info, "description", None),
            }
        return fields

    def _extract_fallback_fields(self) -> dict[str, dict[str, object]]:
        """Extract fields using type hints or basic fallback."""
        try:
            type_hints = cast(dict[str, object], get_type_hints(self.model_class))
            fields: dict[str, dict[str, object]] = {}
            for field_name, field_type in type_hints.items():
                if not field_name.startswith("_"):
                    fields[field_name] = {
                        "type": field_type,
                        "required": True,
                        "description": None,
                    }
            return fields
        except (NameError, AttributeError):
            return self._get_basic_fallback_fields()

    def _get_basic_fallback_fields(self) -> dict[str, dict[str, object]]:
        """Return basic fallback fields when all else fails."""
        return {
            "id": {"type": str, "required": False, "description": "ID"},
            "name": {"type": str, "required": False, "description": "Name"},
            "created_at": {
                "type": datetime,
                "required": False,
                "description": "Created at",
            },
        }

    def _get_openapi_type(self, python_type: type) -> dict[str, object]:
        """Convert Python type to OpenAPI type."""
        # Handle List types
        origin = get_origin(python_type)
        if origin is list:
            args = get_args(python_type)
            item_type: type = args[0] if args else str
            return {"type": "array", "items": self._get_openapi_type(item_type)}
        # Handle Union types (including Optional)
        elif origin is Union:
            args = get_args(python_type)
            # For Optional[T] which is Union[T, None], use T
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return self._get_openapi_type(non_none_args[0])

        result = self.TYPE_MAPPING.get(python_type, {"type": "string"})
        return cast(dict[str, object], result)

    def generate_field_schema(self, field_name: str, field_info: dict[str, object]) -> dict[str, object]:
        """Generate schema for a field."""
        field_type = self._get_openapi_type(cast(type, field_info["type"]))

        # Determine applicable operators
        if field_type["type"] == "string":
            ops = ["$eq", "$ne", "$in", "$nin", "$regex", "$exists"]
        elif field_type["type"] in ["integer", "number"]:
            ops = ["$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$nin", "$exists"]
        else:
            ops = ["$eq", "$ne", "$in", "$nin", "$exists"]

        examples = {}
        if field_type["type"] in ["integer", "number"]:
            examples = {"$gte": 10, "$lte": 100}
        else:
            examples = {"$ne": "excluded"}

        return {
            "anyOf": [
                {**field_type, "description": f"Direct value for {field_name}"},
                {
                    "type": "object",
                    "description": f"Operators for {field_name}: {', '.join(ops)}",
                    "additionalProperties": True,
                    "example": examples,
                },
            ]
        }

    def generate_filter_schema(self) -> dict[str, object]:
        """Generate complete filter schema."""
        properties: dict[str, object] = {}

        # Add field schemas
        for field_name, field_info in self.model_fields.items():
            properties[field_name] = self.generate_field_schema(field_name, field_info)

        # Add logical operators
        logical_operators: dict[str, object] = {
            "$and": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Logical AND - all conditions must be true",
            },
            "$or": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Logical OR - at least one condition must be true",
            },
            "$not": {
                "type": "object",
                "description": "Logical NOT - condition must be false",
            },
        }
        properties.update(logical_operators)

        return {
            "type": "object",
            "description": f"Filter for {self.model_class.__name__}",
            "properties": {
                "where": {
                    "type": "object",
                    "description": "Filter conditions",
                    "properties": properties,
                    "additionalProperties": False,
                },
                "order": {
                    "type": "string",
                    "description": "Sort order (field names, prefix '-' for descending)",
                    "example": "name,-created_at",
                },
                "fields": {
                    "type": "object",
                    "description": "Field selection",
                    "additionalProperties": {"type": "boolean"},
                    "example": {list(self.model_fields.keys())[0]: True} if self.model_fields else {},
                },
            },
            "additionalProperties": False,
        }

    def generate_examples(self) -> dict[str, object]:
        """Generate example queries."""
        if not self.model_fields:
            return {}

        field_names = list(self.model_fields.keys())
        first_field = field_names[0]

        examples: dict[str, object] = {
            "simple": {
                "summary": "Simple equality",
                "description": "Filter by field value",
                "value": f'{{"where":{{"{first_field}":"example"}}}}',
            },
            "operators": {
                "summary": "Using operators",
                "description": "Filter with comparison operators",
                "value": f'{{"where":{{"{first_field}":{{"$ne":"excluded"}}}}}}',
            },
        }

        if len(field_names) >= 2:
            logical_example = (
                f'{{"where":{{"$or":[{{"{field_names[0]}":"value1"}},'
                f'{{"{field_names[1]}":{{"$in":["opt1","opt2"]}}}}]}}}}'
            )
            examples["logical"] = {
                "summary": "Logical operators",
                "description": "Complex queries with $and, $or",
                "value": logical_example,
            }

        complete_example = (
            f'{{"where":{{"{first_field}":{{"$exists":true}}}},'
            f'"order":"{first_field}","fields":{{"{first_field}":true}}}}'
        )
        examples["complete"] = {
            "summary": "Complete query",
            "description": "With filtering, sorting, and field selection",
            "value": complete_example,
        }

        return examples


def generate_filter_docs(model_class: type) -> dict[str, object]:
    """
    Generate comprehensive OpenAPI documentation for filters.

    Args:
        model_class: Model class to document

    Returns:
        dictionary with schemas and examples for OpenAPI spec
    """
    generator = FilterSchemaGenerator(model_class)
    schema = generator.generate_filter_schema()
    examples = generator.generate_examples()

    parameter_schema = {
        "name": "filter",
        "in": "query",
        "required": False,
        "description": (
            f"Filter specification for {model_class.__name__} queries. Provide as JSON string or nested URL parameters."
        ),
        "schema": {
            "type": "string",
            "description": "JSON filter specification",
            "example": '{"where":{"name":"example"},"order":"name"}',
        },
        "examples": examples,
    }

    return {
        "schemas": {f"{model_class.__name__}Filter": schema},
        "parameters": {f"{model_class.__name__}FilterParam": parameter_schema},
        "examples": examples,
    }


def add_filter_docs_to_endpoint(model_class: type):
    """
    Decorator to add filter documentation to FastAPI endpoint.

    Usage:
        @app.get("/products")
        @add_filter_docs_to_endpoint(Product)
        def get_products(filter_query: dict = Depends(query_engine)):
            ...
    """
    from typing import Callable, TypeVar

    F = TypeVar("F", bound=Callable[..., object])

    def decorator(func: F) -> F:
        # Add to function metadata for FastAPI to pick up
        if not hasattr(func, "__annotations__"):
            setattr(func, "__annotations__", {})

        docs = generate_filter_docs(model_class)

        # Store docs in function for potential use by FastAPI
        setattr(func, "_filter_docs", docs)

        return func

    return decorator
