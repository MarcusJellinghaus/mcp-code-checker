"""Tests for the MCP server configuration data model."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.config.servers import (
    MCP_CODE_CHECKER,
    ParameterDef,
    ServerConfig,
    ServerRegistry,
    registry,
)


class TestParameterDef:
    """Test the ParameterDef class."""

    def test_valid_parameter_creation(self) -> None:
        """Test creating valid parameters."""
        # String parameter
        param = ParameterDef(
            name="test-param",
            arg_name="--test-param",
            param_type="string",
            help="Test parameter",
        )
        assert param.name == "test-param"
        assert param.arg_name == "--test-param"
        assert param.param_type == "string"
        assert not param.required

        # Boolean flag
        flag = ParameterDef(
            name="verbose",
            arg_name="--verbose",
            param_type="boolean",
            is_flag=True,
            default=False,
        )
        assert flag.is_flag
        assert flag.default is False

        # Choice parameter
        choice = ParameterDef(
            name="level",
            arg_name="--level",
            param_type="choice",
            choices=["low", "medium", "high"],
            default="medium",
        )
        assert choice.choices == ["low", "medium", "high"]
        assert choice.default == "medium"

    def test_invalid_parameter_type(self) -> None:
        """Test that invalid parameter types raise errors."""
        with pytest.raises(ValueError, match="Invalid param_type"):
            ParameterDef(name="test", arg_name="--test", param_type="invalid")

    def test_empty_name_validation(self) -> None:
        """Test that empty names are rejected."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            ParameterDef(name="", arg_name="--test", param_type="string")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            ParameterDef(name="test", arg_name="", param_type="string")

    def test_choice_parameter_validation(self) -> None:
        """Test choice parameter validation."""
        # No choices provided
        with pytest.raises(ValueError, match="must have a non-empty choices list"):
            ParameterDef(name="level", arg_name="--level", param_type="choice")

        # Empty choices list
        with pytest.raises(ValueError, match="must have at least one choice"):
            ParameterDef(
                name="level", arg_name="--level", param_type="choice", choices=[]
            )

    def test_boolean_flag_validation(self) -> None:
        """Test boolean flag validation."""
        # Valid boolean flag with boolean default
        param = ParameterDef(
            name="flag",
            arg_name="--flag",
            param_type="boolean",
            is_flag=True,
            default=True,
        )
        assert param.default is True

        # Invalid non-boolean default for flag
        with pytest.raises(ValueError, match="must have a boolean default"):
            ParameterDef(
                name="flag",
                arg_name="--flag",
                param_type="boolean",
                is_flag=True,
                default="not_a_bool",
            )


class TestServerConfig:
    """Test the ServerConfig class."""

    def test_mcp_code_checker_configuration(self) -> None:
        """Test that MCP Code Checker configuration is complete."""
        assert MCP_CODE_CHECKER.name == "mcp-code-checker"
        assert MCP_CODE_CHECKER.display_name == "MCP Code Checker"
        assert MCP_CODE_CHECKER.main_module == "src/main.py"
        assert len(MCP_CODE_CHECKER.parameters) == 8

        # Check all parameter names are present
        param_names = [p.name for p in MCP_CODE_CHECKER.parameters]
        expected_names = [
            "project-dir",
            "python-executable",
            "venv-path",
            "test-folder",
            "keep-temp-files",
            "log-level",
            "log-file",
            "console-only",
        ]
        assert set(param_names) == set(expected_names)

    def test_generate_args_basic(self) -> None:
        """Test basic argument generation."""
        config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="main.py",
            parameters=[
                ParameterDef(
                    name="input", arg_name="--input", param_type="string", required=True
                ),
                ParameterDef(name="output", arg_name="--output", param_type="string"),
            ],
        )

        args = config.generate_args({"input": "test.txt", "output": "out.txt"})
        assert args == ["main.py", "--input", "test.txt", "--output", "out.txt"]

    def test_generate_args_with_flags(self) -> None:
        """Test argument generation with boolean flags."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="verbose",
                    arg_name="--verbose",
                    param_type="boolean",
                    is_flag=True,
                ),
                ParameterDef(
                    name="quiet", arg_name="--quiet", param_type="boolean", is_flag=True
                ),
            ],
        )

        # Only verbose flag set
        args = config.generate_args({"verbose": True, "quiet": False})
        assert args == ["test.py", "--verbose"]

        # Both flags set
        args = config.generate_args({"verbose": True, "quiet": True})
        assert "--verbose" in args
        assert "--quiet" in args

    def test_generate_args_with_defaults(self) -> None:
        """Test argument generation using default values."""
        config = ServerConfig(
            name="test",
            display_name="Test",
            main_module="test.py",
            parameters=[
                ParameterDef(
                    name="level",
                    arg_name="--level",
                    param_type="choice",
                    choices=["low", "high"],
                    default="low",
                )
            ],
        )

        # Use default
        args = config.generate_args({})
        assert args == ["test.py", "--level", "low"]

        # Override default
        args = config.generate_args({"level": "high"})
        assert args == ["test.py", "--level", "high"]

    def test_generate_args_mcp_code_checker(self) -> None:
        """Test argument generation for MCP Code Checker."""
        params = {
            "project-dir": "/path/to/project",
            "log-level": "DEBUG",
            "keep-temp-files": True,
            "test-folder": "custom_tests",
        }

        args = MCP_CODE_CHECKER.generate_args(params)

        assert args[0] == "src/main.py"
        assert "--project-dir" in args
        assert "/path/to/project" in args
        assert "--log-level" in args
        assert "DEBUG" in args
        assert "--keep-temp-files" in args
        assert "--test-folder" in args
        assert "custom_tests" in args

    def test_get_required_params(self) -> None:
        """Test getting required parameters."""
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
                    name="optional",
                    arg_name="--optional",
                    param_type="string",
                    required=False,
                ),
                ParameterDef(
                    name="required2",
                    arg_name="--required2",
                    param_type="string",
                    required=True,
                ),
            ],
        )

        required = config.get_required_params()
        assert set(required) == {"required1", "required2"}
        assert "optional" not in required

    def test_validate_project_mcp_code_checker(self) -> None:
        """Test project validation for MCP Code Checker."""
        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Initially invalid (missing structure)
            assert not MCP_CODE_CHECKER.validate_project(project_dir)

            # Create expected structure
            src_dir = project_dir / "src"
            src_dir.mkdir()
            main_file = src_dir / "main.py"
            main_file.write_text("# Main module")

            # Now valid
            assert MCP_CODE_CHECKER.validate_project(project_dir)

    def test_get_parameter_by_name(self) -> None:
        """Test parameter lookup by name."""
        param = MCP_CODE_CHECKER.get_parameter_by_name("project-dir")
        assert param is not None
        assert param.name == "project-dir"
        assert param.required is True

        param = MCP_CODE_CHECKER.get_parameter_by_name("log-level")
        assert param is not None
        assert param.param_type == "choice"
        assert param.default == "INFO"

        # Non-existent parameter
        param = MCP_CODE_CHECKER.get_parameter_by_name("non-existent")
        assert param is None


class TestServerRegistry:
    """Test the ServerRegistry class."""

    def test_register_and_get(self) -> None:
        """Test server registration and retrieval."""
        registry_test = ServerRegistry()

        config = ServerConfig(
            name="test-server", display_name="Test Server", main_module="test.py"
        )

        registry_test.register(config)
        retrieved = registry_test.get("test-server")

        assert retrieved is not None
        assert retrieved.name == "test-server"
        assert retrieved.display_name == "Test Server"

    def test_duplicate_registration(self) -> None:
        """Test that duplicate registrations are rejected."""
        registry_test = ServerRegistry()

        config1 = ServerConfig(
            name="duplicate", display_name="First", main_module="first.py"
        )
        config2 = ServerConfig(
            name="duplicate", display_name="Second", main_module="second.py"
        )

        registry_test.register(config1)

        with pytest.raises(ValueError, match="already registered"):
            registry_test.register(config2)

    def test_list_servers(self) -> None:
        """Test listing registered servers."""
        registry_test = ServerRegistry()

        # Empty registry
        assert registry_test.list_servers() == []

        # Add servers
        for name in ["zebra", "alpha", "beta"]:
            config = ServerConfig(
                name=name,
                display_name=f"{name.title()} Server",
                main_module=f"{name}.py",
            )
            registry_test.register(config)

        # Should be sorted
        assert registry_test.list_servers() == ["alpha", "beta", "zebra"]

    def test_get_all_configs(self) -> None:
        """Test getting all configurations."""
        registry_test = ServerRegistry()

        config1 = ServerConfig(
            name="server1", display_name="Server 1", main_module="s1.py"
        )
        config2 = ServerConfig(
            name="server2", display_name="Server 2", main_module="s2.py"
        )

        registry_test.register(config1)
        registry_test.register(config2)

        all_configs = registry_test.get_all_configs()
        assert len(all_configs) == 2
        assert "server1" in all_configs
        assert "server2" in all_configs
        assert all_configs["server1"].display_name == "Server 1"

    def test_empty_registry(self) -> None:
        """Test empty registry behavior."""
        registry_test = ServerRegistry()

        assert registry_test.get("non-existent") is None
        assert registry_test.list_servers() == []
        assert registry_test.get_all_configs() == {}


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_mcp_code_checker_registered(self) -> None:
        """Test that MCP Code Checker is registered in global registry."""
        config = registry.get("mcp-code-checker")
        assert config is not None
        assert config.name == "mcp-code-checker"
        assert len(config.parameters) == 8

    def test_registry_completeness(self) -> None:
        """Test that the global registry has expected servers."""
        servers = registry.list_servers()
        assert "mcp-code-checker" in servers
