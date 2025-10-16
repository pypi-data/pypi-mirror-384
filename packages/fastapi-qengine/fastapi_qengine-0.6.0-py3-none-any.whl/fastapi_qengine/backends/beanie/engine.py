"""
Beanie query engine.

This module contains the BeanieQueryEngine class for high-level query operations on Beanie models.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Generic, TypeAlias, TypeVar, cast, get_args, get_origin

from beanie import Document
from beanie.odm.queries.aggregation import AggregationQuery
from pydantic import BaseModel, TypeAdapter, create_model
from pydantic import ValidationError as PydanticValidationError
from pydantic.fields import Field, FieldInfo

from fastapi_qengine.core.errors import ValidationError
from fastapi_qengine.core.types import (
    ASTNode,
    ComparisonOperator,
    FieldCondition,
    FilterAST,
    FilterValue,
    LogicalCondition,
    OrderNode,
    SecurityPolicy,
)

from .compiler import BeanieQueryCompiler

# Type variable for Document subclasses
TDocument = TypeVar(name="TDocument", bound=Document)

# Type alias for Beanie query result tuple
BeanieQueryResult: TypeAlias = tuple[
    AggregationQuery[TDocument],
    type[BaseModel] | None,
    str | list[tuple[str, int]] | None,
]


class _ProjectionBase(BaseModel):
    """Base class for projection models."""

    pass


class BeanieQueryEngine(Generic[TDocument]):
    """High-level query engine for Beanie models."""

    def __init__(
        self,
        model_class: type[TDocument],
        security_policy: SecurityPolicy | None = None,
    ) -> None:
        """
        Initialize query engine for a Beanie model.

        Args:
            model_class: Beanie Document class
            security_policy: Optional security policy for controlling field access
        """
        self.model_class: type[TDocument] = model_class
        self.compiler: BeanieQueryCompiler = BeanieQueryCompiler()
        self.security_policy: SecurityPolicy | None = security_policy
        self._field_type_cache: dict[str, object] = {}

    def build_query(self, ast: FilterAST) -> BeanieQueryResult[TDocument]:
        """
        Build a Beanie aggregation query from FilterAST.

        Args:
            ast: FilterAST to compile

        Returns:
            Tuple containing:
            - query: AggregationQuery (with projection model or dict results)
            - projection_model: Optional[type[DocumentProjectionType]]
            - sort: Union[None, str, list[tuple[str, SortDirection]]]
        """
        # Pre-process AST to validate and transform field values
        validated_ast: FilterAST = self._validate_and_transform_ast(ast)

        query_components: dict[str, object] = self.compiler.compile(ast=validated_ast)

        # Build aggregation pipeline stages
        pipeline: list[dict[str, object]] = []

        # Apply filter as $match stage
        self._build_filter_stage(query_components, pipeline)

        # Apply sort as $sort stage
        sort_spec = self._build_sort_stage(query_components, pipeline)

        # Handle projection as $project stage
        projection_model = self._build_projection_stage(query_components, pipeline)

        # Create aggregation query with the pipeline
        query = self._create_aggregation_query(pipeline, projection_model)

        return (
            query,
            projection_model,
            sort_spec,
        )

    def _build_filter_stage(self, query_components: dict[str, object], pipeline: list[dict[str, object]]) -> None:
        """
        Build and append filter stage to the aggregation pipeline.

        Args:
            query_components: Compiled query components
            pipeline: Aggregation pipeline to append to
        """
        if "filter" in query_components:
            filter_dict_raw = cast(dict[str, object], query_components["filter"])
            # Convert enum instances to their values for MongoDB compatibility
            filter_dict = cast(dict[str, object], self._convert_enums_to_values(filter_dict_raw))
            pipeline.append({"$match": filter_dict})

    def _build_sort_stage(
        self, query_components: dict[str, object], pipeline: list[dict[str, object]]
    ) -> str | list[tuple[str, int]] | None:
        """
        Build and append sort stage to the aggregation pipeline.

        Args:
            query_components: Compiled query components
            pipeline: Aggregation pipeline to append to

        Returns:
            Sort specification for result tuple
        """
        if "sort" not in query_components:
            return None

        raw_sort = query_components["sort"]
        sort_spec = self._process_sort_data(raw_sort, pipeline)
        return sort_spec

    def _process_sort_data(
        self, raw_sort: object, pipeline: list[dict[str, object]]
    ) -> str | list[tuple[str, int]] | None:
        """
        Process sort data and append sort stage to pipeline.

        Args:
            raw_sort: Raw sort specification (string or list)
            pipeline: Aggregation pipeline to append to

        Returns:
            Processed sort specification
        """
        if isinstance(raw_sort, str):
            return self._process_string_sort(raw_sort, pipeline)
        elif isinstance(raw_sort, list):
            return self._process_list_sort(cast(list[object], raw_sort), pipeline)

        return None

    def _process_string_sort(self, sort_spec: str, pipeline: list[dict[str, object]]) -> str:
        """
        Process string sort specification.

        Args:
            sort_spec: String sort specification (e.g., "field1,-field2")
            pipeline: Aggregation pipeline to append to

        Returns:
            Original sort specification string
        """
        sort_dict = self._parse_string_sort_fields(sort_spec)
        pipeline.append({"$sort": sort_dict})
        return sort_spec

    def _process_list_sort(self, sort_spec: list[object], pipeline: list[dict[str, object]]) -> list[tuple[str, int]]:
        """
        Process list sort specification.

        Args:
            sort_spec: List of (field, direction) tuples
            pipeline: Aggregation pipeline to append to

        Returns:
            Original sort specification list
        """
        sort_dict = self._parse_list_sort_fields(sort_spec)
        pipeline.append({"$sort": sort_dict})
        return cast(list[tuple[str, int]], sort_spec)

    def _parse_string_sort_fields(self, sort_spec: str) -> dict[str, int]:
        """
        Parse string sort specification into MongoDB sort dictionary.

        Args:
            sort_spec: Comma-separated field list with optional '-' prefix for descending

        Returns:
            MongoDB sort dictionary with field names as keys and sort directions as values
        """
        sort_dict: dict[str, int] = {}
        fields = sort_spec.split(",")

        for field in fields:
            field = field.strip()
            if field.startswith("-"):
                sort_dict[field[1:]] = -1
            else:
                sort_dict[field] = 1

        return sort_dict

    def _parse_list_sort_fields(self, sort_spec: list[object]) -> dict[str, int]:
        """
        Parse list sort specification into MongoDB sort dictionary.

        Args:
            sort_spec: List of (field, direction) tuples where direction is 1 (asc) or -1 (desc)

        Returns:
            MongoDB sort dictionary with field names as keys and sort directions as values
        """
        sort_dict: dict[str, int] = {}

        for item in sort_spec:
            if isinstance(item, (list, tuple)):
                item_cast: list[object] | tuple[object, ...] = cast(list[object] | tuple[object, ...], item)
                if len(item_cast) == 2:
                    field, direction = item_cast
                    # Direction should be 1 (ascending) or -1 (descending)
                    if isinstance(direction, int) and direction in (1, -1):
                        sort_dict[cast(str, field)] = direction

        return sort_dict

    def _build_projection_stage(
        self, query_components: dict[str, object], pipeline: list[dict[str, object]]
    ) -> type[BaseModel] | None:
        """
        Build and append projection stage to the aggregation pipeline.

        Args:
            query_components: Compiled query components
            pipeline: Aggregation pipeline to append to

        Returns:
            Projection model for result tuple
        """
        projection_model: type[BaseModel] | None = None
        if "projection" in query_components:
            projection_dict_raw = query_components["projection"]
            if isinstance(projection_dict_raw, dict):
                projection_dict = cast(dict[str, int], projection_dict_raw)
                # Create a dynamic projection model for fastapi-pagination
                projection_model = self._create_projection_model(projection_dict)
                # Add $project stage to pipeline
                pipeline.append({"$project": projection_dict})
        else:
            # No projection specified - create a projection model with all fields
            # to ensure we get Document instances instead of dicts
            all_fields = list(getattr(self.model_class, "model_fields", {}).keys())
            projection_dict = dict.fromkeys(all_fields, 1)
            projection_model = self._create_projection_model(projection_dict)
            # Don't add $project stage for all fields - let Beanie handle it

        return projection_model

    def _create_aggregation_query(
        self, pipeline: list[dict[str, object]], projection_model: type[BaseModel] | None
    ) -> AggregationQuery[TDocument]:
        """
        Create aggregation query from pipeline and projection model.

        Args:
            pipeline: Aggregation pipeline stages
            projection_model: Projection model for typed results

        Returns:
            Configured aggregation query
        """
        # Always use projection_model to get typed results
        if projection_model:
            query = cast(
                AggregationQuery[TDocument],
                self.model_class.aggregate(pipeline, projection_model=projection_model),  # pyright: ignore[reportUnknownMemberType]
            )
        else:
            # Fallback - should not happen with the logic above
            query = cast(
                AggregationQuery[TDocument],
                self.model_class.aggregate(pipeline),  # pyright: ignore[reportUnknownMemberType]
            )

        return query

    def _validate_and_transform_ast(self, ast: FilterAST) -> FilterAST:
        """
        Validate and transform values in the AST according to model field types.

        Args:
            ast: Original FilterAST

        Returns:
            Transformed FilterAST with validated values
        """
        if ast.where:
            ast.where = self._validate_and_transform_node(ast.where)

        # Order nodes validation - ensure fields exist
        if ast.order:
            validated_order: list[OrderNode] = []
            for order_node in ast.order:
                try:
                    self._validate_field_exists(order_node.field)
                    validated_order.append(order_node)
                except ValidationError:
                    # Skip invalid order fields
                    continue
            ast.order = validated_order

        # Fields validation - ensure fields exist
        if ast.fields:
            validated_fields = {}
            for field, include in ast.fields.fields.items():
                base_field = field.split(".", 1)[0]  # For dot notation, check at least the base field
                try:
                    self._validate_field_exists(base_field)
                    validated_fields[field] = include
                except ValidationError:
                    # Skip invalid fields
                    continue
            ast.fields.fields = validated_fields

        return ast

    def _validate_and_transform_node(self, node: ASTNode) -> ASTNode:
        """
        Recursively validate and transform a node in the AST.

        Args:
            node: AST node to validate and transform

        Returns:
            Validated and transformed AST node
        """
        if isinstance(node, FieldCondition):
            # Validate field existence
            self._validate_field_exists(node.field)

            # Transform value based on field type
            transformed_value = self._transform_value(node.field, node.operator, node.value)
            return FieldCondition(
                field=node.field,
                operator=node.operator,
                value=cast(FilterValue, transformed_value),
            )

        elif isinstance(node, LogicalCondition):
            # Recursively validate and transform each condition
            transformed_conditions = [self._validate_and_transform_node(condition) for condition in node.conditions]
            return LogicalCondition(
                operator=node.operator,
                conditions=transformed_conditions,
            )

        return node

    def _validate_field_exists(self, field_path: str) -> None:
        """
        Validate that a field exists in the model.

        Args:
            field_path: Field path (can use dot notation)

        Raises:
            ValidationError: If the field doesn't exist in the model
        """
        parts = field_path.split(".", 1)
        field_name = parts[0]

        # Skip validation for special MongoDB operators or metadata fields
        if field_name.startswith("$") or field_name == "_id" or field_name == "id":
            return

        # Check if field exists in model
        model_fields = getattr(self.model_class, "model_fields", {})
        if field_name not in model_fields:
            model_name = getattr(self.model_class, "__name__", "Unknown")
            raise ValidationError(
                f"Field '{field_name}' does not exist in model '{model_name}'",
                field=field_name,
            )

    def _get_field_type(self, field_name: str) -> object:
        """
        Get the type of a field from the model.

        Args:
            field_name: Field name

        Returns:
            Type of the field
        """
        # Use cached type if available
        if field_name in self._field_type_cache:
            return self._field_type_cache[field_name]

        # Get field type from model
        model_fields: dict[str, FieldInfo] = getattr(self.model_class, "model_fields", {})
        if field_name not in model_fields:
            return object

        field_info = model_fields[field_name]
        field_type: object = field_info.annotation or object

        # Unwrap Optional/Union types
        origin = get_origin(field_type)
        if origin is not None:
            origin = cast(object, origin)
            # Check if it's a Union (which includes Optional)
            type_name = getattr(origin, "__name__", str(origin))
            if "Union" in str(origin) or type_name == "UnionType":
                args = cast(tuple[object, object], get_args(field_type))
                # Remove None from Union args to get the base type
                non_none_args: list[object] = [arg for arg in args if arg is not type(None)]  # noqa: E721
                if len(non_none_args) == 1:
                    field_type = non_none_args[0]

        # Cache the type
        self._field_type_cache[field_name] = field_type
        return field_type

    def _transform_value(self, field_path: str, operator: ComparisonOperator | str, value: object) -> object:
        """
        Transform a value based on the field type and operator.

        Args:
            field_path: Field path
            operator: Comparison operator (enum or string)
            value: Original value

        Returns:
            Transformed value (scalar or list)
        """
        parts = field_path.split(".", 1)
        field_name = parts[0]

        # Skip transformation for special MongoDB operators
        if field_name.startswith("$"):
            return value

        # Normalize operator to enum
        if isinstance(operator, str):
            try:
                operator = ComparisonOperator(operator)
            except ValueError:
                # If not a valid operator, treat as EQ
                operator = ComparisonOperator.EQ

        field_type = self._get_field_type(field_name)

        # Handle lists for $in and $nin operators
        if operator in (ComparisonOperator.IN, ComparisonOperator.NIN) and isinstance(value, list):
            try:
                raw_list = cast(list[object], value)
                transformed_list: list[object] = [
                    self._transform_scalar_value(field_type, item, field_path) for item in raw_list
                ]
                return transformed_list
            except Exception as e:
                # Cast to object to avoid partially unknown type diagnostics
                raise ValidationError(
                    f"Failed to transform list value for field '{field_path}': {e}",
                    field=field_path,
                    value=cast(object, value),
                ) from e

        # Handle scalar values
        try:
            return self._transform_scalar_value(field_type, value, field_path)
        except Exception as e:
            raise ValidationError(
                f"Failed to transform value for field '{field_path}': {e}",
                field=field_path,
                value=cast(list[object], value),
            ) from e

    def _transform_scalar_value(self, field_type: object, value: object, field_path: str) -> object:
        """
        Transform a scalar value based on field type.

        Args:
            field_type: Type of the field
            value: Original value
            field_path: Field path (for error reporting)

        Returns:
            Transformed value
        """
        _ = field_path
        # Skip None values
        if value is None:
            return None

        # Handle common type transformations

        # ObjectId fields
        if (
            hasattr(field_type, "__name__")
            and getattr(field_type, "__name__", None) == "PydanticObjectId"
            and isinstance(value, str)
        ):
            from beanie.odm.fields import PydanticObjectId

            return PydanticObjectId(value)

        # DateTime fields
        if field_type == datetime and isinstance(value, str):
            return datetime.fromisoformat(value)

        # Date fields
        if field_type == date and isinstance(value, str):
            parsed_date = date.fromisoformat(value)
            # Convert to datetime at start of day for MongoDB compatibility
            return datetime.combine(parsed_date, datetime.min.time())

        # Enum fields
        if isinstance(field_type, type) and issubclass(field_type, Enum) and not isinstance(value, Enum):
            try:
                if isinstance(value, str) and hasattr(field_type, value):
                    return cast(object, getattr(field_type, value))
                return field_type(value)
            except (ValueError, KeyError, AttributeError):
                # If conversion fails, return original value
                return value

        # Use Pydantic for complex type validation/conversion
        try:
            adapter: TypeAdapter[object] = TypeAdapter(field_type)
            return adapter.validate_python(value)
        except PydanticValidationError:
            # If Pydantic validation fails, return original value
            # This allows MongoDB to handle the comparison as it sees fit
            return value

    def _create_projection_model(self, projection_dict: dict[str, int]) -> type[BaseModel] | None:
        """
        Crea un modelo Pydantic para usar con .project() en Beanie
        a partir de un dict de proyección con soporte dot-notation.

        Reglas:
          - Si hay al menos un '1' => modo INCLUSIÓN (los '0' se ignoran).
          - Si NO hay '1' => modo EXCLUSIÓN toplevel (incluye todos menos los '0' a primer nivel).
          - Aplica security policy para filtrar campos permitidos/bloqueados.
        """
        # Apply security policy to filter projection fields
        filtered_projection: dict[str, int] = self._apply_security_policy_to_projection(projection_dict)

        if not filtered_projection:
            # Si la security policy bloquea todos los campos, retornar None
            return None

        include_paths: list[str] = [key for key, val in filtered_projection.items() if val == 1]

        if include_paths:
            tree = self._paths_to_tree(include_paths)
        else:
            # Exclusión de primer nivel
            exclude_top: set[str] = {key.split(".", 1)[0] for key, val in filtered_projection.items() if val == 0}

            # Tipado explícito para evitar object
            model_fields: dict[str, FieldInfo] = getattr(self.model_class, "model_fields", {})
            to_include: list[str] = [field_name for field_name in model_fields.keys() if field_name not in exclude_top]

            # Apply security policy to the list of fields to include
            to_include = self._filter_fields_by_policy(to_include)

            if not to_include:
                return None
            tree = self._paths_to_tree(to_include)

        model_name = f"{getattr(self.model_class, '__name__', 'Unknown')}Projection"
        try:
            base_model_class: type[BaseModel] = cast(type[BaseModel], self.model_class)
            projection_model: type[BaseModel] = self._build_model_from_tree(base_model_class, tree, model_name)
            return projection_model
        except Exception:
            # Fallback suave: si algo falla, no forzamos proyección
            return None

    def _apply_security_policy_to_projection(self, projection_dict: dict[str, int]) -> dict[str, int]:
        """
        Apply security policy to filter projection dictionary.

        Args:
            projection_dict: Original projection dictionary

        Returns:
            Filtered projection dictionary respecting security policy
        """
        if self.security_policy is None:
            return projection_dict

        filtered: dict[str, int] = {}
        for field, value in projection_dict.items():
            # Extract base field name (for dot notation support)
            base_field = field.split(".", 1)[0]

            # Check if field is blocked
            blocked_fields = self.security_policy.blocked_fields
            if blocked_fields and base_field in blocked_fields:
                continue

            # Check if field is in allowed list (if whitelist is defined)
            allowed_fields = self.security_policy.allowed_fields
            if allowed_fields and base_field not in allowed_fields:
                continue

            filtered[field] = value

        return filtered

    def _filter_fields_by_policy(self, fields: list[str]) -> list[str]:
        """
        Filter a list of field names based on security policy.

        Args:
            fields: list of field names

        Returns:
            Filtered list of field names
        """
        if self.security_policy is None:
            return fields

        filtered: list[str] = []
        for field in fields:
            # Check if field is blocked
            blocked_fields = self.security_policy.blocked_fields
            if blocked_fields is not None and field in blocked_fields:
                continue

            # Check if field is in allowed list (if whitelist is defined)
            allowed_fields = self.security_policy.allowed_fields
            if allowed_fields is not None and field not in allowed_fields:
                continue

            filtered.append(field)

        return filtered

    @staticmethod
    def _paths_to_tree(paths: list[str]) -> dict[str, object]:
        """
        Convert list of field paths to nested tree structure.

        Example: ["a", "b.c", "b.d.e"] -> {"a": True, "b": {"c": True, "d": {"e": True}}}

        Args:
            paths: List of field paths

        Returns:
            Nested dictionary representing the tree structure
        """
        root: dict[str, object] = {}
        for p in paths:
            node: dict[str, object] = root
            parts = p.split(".")
            for i, part in enumerate(parts):
                last = i == len(parts) - 1
                if last:
                    node[part] = True
                else:
                    if part not in node:
                        node[part] = {}
                    next_node = node[part]
                    if isinstance(next_node, dict):
                        node = cast(dict[str, object], next_node)
        return root

    @staticmethod
    def _unwrap_optional_union(tp: type) -> type:
        """
        Unwrap Optional/Union types to get the base type.

        Args:
            tp: Type to unwrap

        Returns:
            Unwrapped base type
        """
        origin = get_origin(tp)
        if origin is not None:
            origin = cast(object, origin)
            # Check if it's a Union (which includes Optional)
            type_name = getattr(origin, "__name__", str(origin))
            if "Union" in str(origin) or type_name == "UnionType":
                args = cast(tuple[object, object], get_args(tp))
                non_none_args = tuple(a for a in args if a is not type(None))  # noqa: E721
                if len(non_none_args) == 1:
                    return cast(type, non_none_args[0])
        return tp

    @staticmethod
    def _is_pyd_model(tp: type) -> bool:
        """
        Check if a type is a Pydantic model.

        Args:
            tp: Type to check

        Returns:
            True if type is a BaseModel subclass
        """
        try:
            return issubclass(tp, BaseModel)
        except TypeError:
            return False

    @staticmethod
    def _is_sequence_of_models(
        tp: object,
    ) -> tuple[bool, type[BaseModel] | None, object | None]:
        """
        Detect if type is list/tuple/set[T] where T is BaseModel.

        Args:
            tp: Type to check

        Returns:
            Tuple of (is_sequence, element_type, origin)
        """
        origin = get_origin(tp)
        if origin in (list, tuple, set):
            args = get_args(tp)
            if not args:
                return (False, None, None)
            elem = cast(type, args[0])
            elem = BeanieQueryEngine._unwrap_optional_union(elem)
            if BeanieQueryEngine._is_pyd_model(elem):
                return (True, cast(type[BaseModel], elem), origin)
        return (False, None, None)

    @staticmethod
    def _optional(tp: object) -> object:
        """
        Make a type optional.

        Args:
            tp: Type to make optional

        Returns:
            Optional version of the type
        """
        return tp or None

    def _build_model_from_tree(
        self,
        model: type[BaseModel],
        tree: dict[str, object],
        model_name: str,
    ) -> type[BaseModel]:
        """
        Build a Pydantic model recursively from a projection tree.

        Leaves -> Optional[T] = None
        Nested nodes -> require Pydantic submodel or collection of submodels

        Args:
            model: Base model to build from
            tree: Projection tree structure
            model_name: Name for the generated model

        Returns:
            Generated Pydantic model

        Raises:
            KeyError: If a field in tree doesn't exist in the model
        """

        field_defs: dict[str, object] = {}

        for name, subtree in tree.items():
            if name not in model.model_fields:
                raise KeyError(f"Campo '{name}' no existe en {model.__name__}")

            f_info = model.model_fields[name]
            f_type = f_info.annotation or object
            f_type = self._unwrap_optional_union(f_type)

            if subtree is True:
                # Leaf: include type as is, but make it Optional
                field_defs[name] = (f_type, Field(default=None))
                continue

            # Nested node
            if self._is_pyd_model(f_type):
                sub_model_name = f"{model_name}_{name.capitalize()}"
                sub_projection = self._build_model_from_tree(
                    cast(type[BaseModel], f_type),
                    cast(dict[str, object], subtree),
                    sub_model_name,
                )
                field_defs[name] = (self._optional(sub_projection), None)
                continue

            is_seq, elem_type, origin = self._is_sequence_of_models(f_type)
            if is_seq and elem_type and origin:
                sub_model_name = f"{model_name}_{name.capitalize()}Item"
                sub_projection = self._build_model_from_tree(
                    elem_type, cast(dict[str, object], subtree), sub_model_name
                )
                # Create the collection type with the projection
                projected_coll = cast(dict[object, object], origin)[sub_projection]
                field_defs[name] = (self._optional(projected_coll), None)
                continue

            # If we reach here with subtree != True, treat as leaf
            field_defs[name] = (self._optional(f_type), None)
        projection: type[BaseModel] = cast(
            type[BaseModel],
            # pyrefly: ignore
            create_model(  # pyright: ignore[reportCallIssue]
                model_name,
                __base__=_ProjectionBase,
                **field_defs,  # pyright: ignore[reportArgumentType]
            ),
        )

        return projection

    def execute_query(self, ast: FilterAST) -> BeanieQueryResult[TDocument]:
        """
        Execute query and return results.

        Args:
            ast: FilterAST to execute

        Returns:
            Tuple containing query object, projection model, and sort specification
        """
        # build_query already includes validation and transformation
        return self.build_query(ast)

    def _convert_enums_to_values(
        self, data: object
    ) -> object | dict[object, object | dict[object, object] | list[object] | object] | list[object] | object:
        """
        Recursively convert enum instances to their values in nested data structures.

        Args:
            data: Input data potentially containing enum instances

        Returns:
            Data with enum instances converted to their values
        """
        if isinstance(data, Enum):
            return cast(object, data.value)
        elif isinstance(data, dict):
            return {
                key: self._convert_enums_to_values(value) for key, value in cast(dict[object, object], data).items()
            }
        elif isinstance(data, list):
            return [self._convert_enums_to_values(item) for item in cast(list[object], data)]
        else:
            return data
