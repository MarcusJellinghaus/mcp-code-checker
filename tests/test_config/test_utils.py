"""Tests for configuration validation utilities."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.config.servers import ParameterDef, ServerConfig
from src.config.utils import (
    normalize_path_parameter,
    validate_parameter_value,
    validate_required_parameters,
)


class TestValidateParameterValue:
    """Test parameter value validation."""

    def test_validate_string_parameter(self) -> None:
        """Test string parameter validation."""
        param = ParameterDef(name="text", arg_name="--text", param_type="string")

        # Valid string values
        assert validate_parameter_value(param, "hello") == []
        assert validate_parameter_value(param, "") == []
        assert validate_parameter_value(param, None) == []

        # Convertible to string
        assert validate_parameter_value(param, 123) == []
        assert validate_parameter_value(param, True) == []

    def test_validate_boolean_parameter(self) -> None:
        """Test boolean parameter validation."""
        param = ParameterDef(name="flag", arg_name="--flag", param_type="boolean")

        # Valid boolean values
        assert validate_parameter_value(param, True) == []
        assert validate_parameter_value(param, False) == []
        assert validate_parameter_value(param, None) == []

        # Invalid values
        errors = validate_parameter_value(param, "true")
        assert len(errors) == 1
        assert "must be a boolean value" in errors[0]

        errors = validate_parameter_value(param, 1)
        assert len(errors) == 1
        assert "must be a boolean value" in errors[0]

    def test_validate_choice_parameter(self) -> None:
        """Test choice parameter validation."""
        param = ParameterDef(
            name="level",
            arg_name="--level",
            param_type="choice",
            choices=["low", "medium", "high"],
        )

        # Valid choices
        assert validate_parameter_value(param, "low") == []
        assert validate_parameter_value(param, "medium") == []
        assert validate_parameter_value(param, "high") == []
        assert validate_parameter_value(param, None) == []

        # Invalid choice
        errors = validate_parameter_value(param, "invalid")
        assert len(errors) == 1
        assert "not in valid choices" in errors[0]
        assert "low, medium, high" in errors[0]

    def test_validate_path_parameter(self) -> None:
        """Test path parameter validation."""
        param = ParameterDef(name="file", arg_name="--file", param_type="path")

        # Valid path values
        assert validate_parameter_value(param, "/path/to/file") == []
        assert validate_parameter_value(param, "relative/path") == []
        assert validate_parameter_value(param, Path("/absolute/path")) == []
        assert validate_parameter_value(param, None) == []

        # Invalid values
        errors = validate_parameter_value(param, 123)
        assert len(errors) == 1
        assert "must be a path string or Path object" in errors[0]

        errors = validate_parameter_value(param, ["not", "a", "path"])
        assert len(errors) == 1
        assert "must be a path string or Path object" in errors[0]


class TestValidateRequiredParameters:
    """Test required parameter validation."""

    def test_all_required_provided(self) -> None:
        """Test when all required parameters are provided."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="required1",
                    arg_name="--required1",
                    param_type="string",
                    required=True,
                ),
                ParameterDef(
                    name="required2",
                    arg_name="--required2",
                    param_type="string",
                    required=True,
                ),
                ParameterDef(
                    name="optional",
                    arg_name="--optional",
                    param_type="string",
                    required=False,
                ),
            ],
        )

        # All required provided
        errors = validate_required_parameters(
            config, {"required1": "value1", "required2": "value2"}
        )
        assert errors == []

        # All required plus optional
        errors = validate_required_parameters(
            config, {"required1": "value1", "required2": "value2", "optional": "opt"}
        )
        assert errors == []

    def test_missing_required_parameters(self) -> None:
        """Test when required parameters are missing."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="required1",
                    arg_name="--required1",
                    param_type="string",
                    required=True,
                ),
                ParameterDef(
                    name="required2",
                    arg_name="--required2",
                    param_type="string",
                    required=True,
                ),
            ],
        )

        # Missing all required
        errors = validate_required_parameters(config, {})
        assert len(errors) == 2
        assert "required1 is required" in errors
        assert "required2 is required" in errors

        # Missing one required
        errors = validate_required_parameters(config, {"required1": "value"})
        assert len(errors) == 1
        assert "required2 is required" in errors

    def test_none_values_treated_as_missing(self) -> None:
        """Test that None values are treated as missing."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="required",
                    arg_name="--required",
                    param_type="string",
                    required=True,
                )
            ],
        )

        errors = validate_required_parameters(config, {"required": None})
        assert len(errors) == 1
        assert "required is required" in errors

    def test_no_required_parameters(self) -> None:
        """Test config with no required parameters."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="optional1",
                    arg_name="--optional1",
                    param_type="string",
                    required=False,
                ),
                ParameterDef(
                    name="optional2",
                    arg_name="--optional2",
                    param_type="string",
                    required=False,
                ),
            ],
        )

        # Empty params is valid
        errors = validate_required_parameters(config, {})
        assert errors == []

        # Any combination is valid
        errors = validate_required_parameters(config, {"optional1": "value"})
        assert errors == []


class TestNormalizePathParameter:
    """Test path normalization."""

    def test_absolute_path_unchanged(self) -> None:
        """Test that absolute paths are returned unchanged."""
        # Use platform-appropriate absolute path
        import platform

        if platform.system() == "Windows":
            abs_path = "C:\\absolute\\path"
            base_path = Path("D:\\base")
        else:
            abs_path = "/absolute/path"
            base_path = Path("/base")

        result = normalize_path_parameter(abs_path, base_path)
        # The result should be the absolute path (normalized by Path)
        assert Path(result).is_absolute()
        assert Path(result) == Path(abs_path).resolve()

    def test_relative_path_resolution(self) -> None:
        """Test that relative paths are resolved relative to base."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Simple relative path
            result = normalize_path_parameter("subdir/file.txt", base_path)
            expected = base_path / "subdir" / "file.txt"
            assert Path(result) == expected.resolve()

            # Current directory
            result = normalize_path_parameter(".", base_path)
            assert Path(result) == base_path.resolve()

            # Parent directory
            result = normalize_path_parameter("..", base_path)
            assert Path(result) == base_path.parent.resolve()

    def test_path_with_dots(self) -> None:
        """Test path normalization with . and .. components."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Path with .
            result = normalize_path_parameter("./subdir/./file.txt", base_path)
            expected = base_path / "subdir" / "file.txt"
            assert Path(result) == expected.resolve()

            # Path with ..
            result = normalize_path_parameter("subdir/../other/file.txt", base_path)
            expected = base_path / "other" / "file.txt"
            assert Path(result) == expected.resolve()

    def test_windows_vs_unix_paths(self) -> None:
        """Test handling of different path separators."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Forward slashes (Unix-style)
            result = normalize_path_parameter("sub/dir/file.txt", base_path)
            expected = base_path / "sub" / "dir" / "file.txt"
            assert Path(result) == expected.resolve()

            # Backslashes (Windows-style) - Path handles this
            result = normalize_path_parameter("sub\\dir\\file.txt", base_path)
            expected = base_path / "sub" / "dir" / "file.txt"
            # Path normalizes separators based on OS
            assert Path(result).name == "file.txt"
