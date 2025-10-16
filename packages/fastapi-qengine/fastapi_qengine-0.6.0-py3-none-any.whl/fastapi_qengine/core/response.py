# pyright: basic
from collections.abc import Iterable

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

from .types import SecurityPolicy


def create_response_model(
    model: type[BaseModel], security_policy: SecurityPolicy | None = None
) -> type[BaseModel]:
    """
    Creates a new Pydantic model with all fields from the original model
    made optional, respecting security policies.

    This is for projection compatibility.

    Args:
        model: The base Pydantic model to create a response model from.
        security_policy: Optional security policy to control which fields can be projected.

    Returns:
        A new Pydantic model with optional fields filtered by security policy.

    Raises:
        ValueError: If security policy results in no fields being available.
    """
    # Get all fields from the model
    all_fields = model.model_fields.items()

    # Apply security policy filtering
    filtered_fields = _filter_fields_by_policy(all_fields, security_policy)

    if not filtered_fields:
        raise ValueError(
            f"Security policy resulted in no available fields for model {model.__name__}. Check allowed_fields and blocked_fields configuration."
        )

    # Create optional fields
    field_definitions: dict[str, object] = {
        name: (field.annotation, Field(default=None))
        for name, field in filtered_fields.items()
    }
    model_name = f"Optional{model.__name__}"

    model_config = model.model_config.copy()
    model_config["from_attributes"] = True
    model_config["use_enum_values"] = True
    model_config["extra"] = "ignore"

    # pyrefly: ignore
    new_model: type[BaseModel] = create_model(  # pyright: ignore[reportCallIssue]
        model_name,
        **field_definitions,  # pyright: ignore[reportArgumentType]
    )
    new_model.model_config = model_config
    return new_model


def _filter_fields_by_policy(
    fields: Iterable[tuple[str, FieldInfo]],
    security_policy: SecurityPolicy | None = None,
) -> dict[str, FieldInfo]:
    """
    Filter fields based on security policy.

    Args:
        fields: Iterable of (field_name, field_info) tuples.
        security_policy: Security policy with allowed_fields and blocked_fields.

    Returns:
        Dictionary of filtered fields {name: field_info}.
    """
    if security_policy is None:
        return {name: field for name, field in fields}

    allowed_fields_set = _get_allowed_fields_set(security_policy)
    blocked_fields_set = _get_blocked_fields_set(security_policy)

    filtered: dict[str, FieldInfo] = {}
    for name, field in fields:
        # Check if field is explicitly blocked
        if name in blocked_fields_set:
            continue

        # If allowed_fields is defined, only include fields in the whitelist
        if allowed_fields_set is not None and name not in allowed_fields_set:
            continue

        filtered[name] = field

    return filtered


def _get_allowed_fields_set(security_policy: SecurityPolicy) -> set[str] | None:
    """Get the set of allowed fields from security policy."""
    if security_policy.allowed_fields is None:
        return None
    return set(security_policy.allowed_fields)


def _get_blocked_fields_set(security_policy: SecurityPolicy) -> set[str]:
    """Get the set of blocked fields from security policy."""
    if security_policy.blocked_fields is None:
        return set()
    return set(security_policy.blocked_fields)
