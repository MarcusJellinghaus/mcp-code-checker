"""Validation utilities for MCP server configurations.

This module provides functions for validating parameter values,
required parameters, and path normalization.
"""

from pathlib import Path
from typing import Any

from src.config.servers import ParameterDef, ServerConfig


def validate_parameter_value(param_def: ParameterDef, value: Any) -> list[str]:
    """Validate a parameter value against its definition.

    Args:
        param_def: Parameter definition to validate against
        value: Value to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Skip validation if value is None (will use default or skip)
    if value is None:
        return errors

    # Type-specific validation
    if param_def.param_type == "choice":
        if param_def.choices and value not in param_def.choices:
            errors.append(
                f"Parameter '{param_def.name}' value '{value}' is not in valid choices: "
                f"{', '.join(param_def.choices)}"
            )

    elif param_def.param_type == "boolean":
        if not isinstance(value, bool):
            errors.append(
                f"Parameter '{param_def.name}' must be a boolean value, got {type(value).__name__}"
            )

    elif param_def.param_type == "path":
        # Path parameters can be strings or Path objects
        if not isinstance(value, (str, Path)):
            errors.append(
                f"Parameter '{param_def.name}' must be a path string or Path object, "
                f"got {type(value).__name__}"
            )

    elif param_def.param_type == "string":
        # String parameters should be convertible to string
        if value is not None and not isinstance(value, str):
            try:
                str(value)
            except (TypeError, ValueError) as e:
                errors.append(
                    f"Parameter '{param_def.name}' cannot be converted to string: {e}"
                )

    return errors


def validate_required_parameters(
    server_config: ServerConfig, user_params: dict[str, Any]
) -> list[str]:
    """Validate that all required parameters are provided.

    Args:
        server_config: Server configuration with parameter definitions
        user_params: User-provided parameters (keys with underscores)

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    for param in server_config.parameters:
        if param.required:
            # Convert parameter name to underscore format to match user_params keys
            param_key = param.name.replace("-", "_")
            if param_key not in user_params or user_params[param_key] is None:
                errors.append(f"{param.name} is required")

    return errors


def normalize_path_parameter(value: str, base_path: Path) -> str:
    """Normalize a path parameter to absolute path.

    Args:
        value: Path value (can be relative or absolute)
        base_path: Base directory for relative paths

    Returns:
        Absolute path as string
    """
    # Convert to Path object
    path = Path(value)

    # If already absolute, return as-is
    if path.is_absolute():
        return str(path)

    # Make relative to base_path
    absolute_path = (base_path / path).resolve()
    return str(absolute_path)
