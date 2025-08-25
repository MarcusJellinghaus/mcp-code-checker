"""Core data model for MCP server configurations.

This module provides the data structures needed to represent, validate,
and generate command-line arguments for MCP servers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParameterDef:
    """Definition of a server parameter for CLI and config generation.

    Attributes:
        name: CLI parameter name (e.g., "project-dir")
        arg_name: Server argument (e.g., "--project-dir")
        param_type: Type of parameter ("string", "boolean", "choice", "path")
        required: Whether the parameter is required
        default: Default value for the parameter
        choices: List of valid choices for "choice" type parameters
        help: Help text for CLI
        is_flag: True for boolean flags (action="store_true")
    """

    name: str
    arg_name: str
    param_type: str
    required: bool = False
    default: Any = None
    choices: list[str] | None = None
    help: str = ""
    is_flag: bool = False

    def __post_init__(self) -> None:
        """Validate parameter definition after creation."""
        # Validate parameter type
        valid_types = {"string", "boolean", "choice", "path"}
        if self.param_type not in valid_types:
            raise ValueError(
                f"Invalid param_type '{self.param_type}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

        # Validate name and arg_name
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Parameter 'name' must be a non-empty string")
        if not self.arg_name or not isinstance(self.arg_name, str):
            raise ValueError("Parameter 'arg_name' must be a non-empty string")

        # Validate choice parameters
        if self.param_type == "choice":
            if self.choices is None or not isinstance(self.choices, list):
                raise ValueError(
                    f"Parameter '{self.name}' of type 'choice' must have a non-empty choices list"
                )
            elif len(self.choices) == 0:
                raise ValueError(
                    f"Parameter '{self.name}' of type 'choice' must have at least one choice"
                )

        # Validate boolean flags
        if self.param_type == "boolean":
            if (
                self.is_flag
                and self.default is not None
                and not isinstance(self.default, bool)
            ):
                raise ValueError(
                    f"Boolean flag parameter '{self.name}' must have a boolean default value"
                )


@dataclass
class ServerConfig:
    """Complete configuration for an MCP server type.

    Attributes:
        name: Internal name of the server (e.g., "mcp-code-checker")
        display_name: Human-readable display name
        main_module: Path to the main module to execute
        parameters: List of all possible parameters for this server
    """

    name: str
    display_name: str
    main_module: str
    parameters: list[ParameterDef] = field(default_factory=list)

    def generate_args(self, user_params: dict[str, Any]) -> list[str]:
        """Generate command line args from user parameters.

        Args:
            user_params: Dictionary of parameter names to values

        Returns:
            List of command-line arguments including the main module
        """
        args = [self.main_module]

        for param in self.parameters:
            # Get value from user params or use default
            value = user_params.get(param.name, param.default)

            # Skip if no value provided
            if value is None:
                continue

            # Handle boolean flags
            if param.is_flag:
                if value:  # Only add flag if True
                    args.append(param.arg_name)
            else:
                # Add parameter and value
                args.append(param.arg_name)
                args.append(str(value))

        return args

    def get_required_params(self) -> list[str]:
        """Get list of required parameter names.

        Returns:
            List of names of required parameters
        """
        return [param.name for param in self.parameters if param.required]

    def validate_project(self, project_dir: Path) -> bool:
        """Check if project is compatible (server-specific logic).

        For MCP Code Checker, validates that the expected structure exists.

        Args:
            project_dir: Path to the project directory

        Returns:
            True if the project is valid for this server
        """
        if self.name == "mcp-code-checker":
            # Check for expected MCP Code Checker structure
            main_path = project_dir / self.main_module
            src_path = project_dir / "src"

            # Both the main module and src directory should exist
            return main_path.exists() and src_path.exists()

        # Default validation for other servers
        return True

    def get_parameter_by_name(self, name: str) -> ParameterDef | None:
        """Get parameter definition by name.

        Args:
            name: Name of the parameter to find

        Returns:
            ParameterDef if found, None otherwise
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None


class ServerRegistry:
    """Registry for server configurations."""

    def __init__(self) -> None:
        """Initialize the server registry."""
        self._servers: dict[str, ServerConfig] = {}

    def register(self, config: ServerConfig) -> None:
        """Register a server configuration.

        Args:
            config: ServerConfig to register

        Raises:
            ValueError: If a server with the same name is already registered
        """
        if config.name in self._servers:
            raise ValueError(f"Server '{config.name}' is already registered")
        self._servers[config.name] = config

    def get(self, name: str) -> ServerConfig | None:
        """Get server configuration by name.

        Args:
            name: Name of the server to retrieve

        Returns:
            ServerConfig if found, None otherwise
        """
        return self._servers.get(name)

    def list_servers(self) -> list[str]:
        """Get list of registered server names.

        Returns:
            Sorted list of server names
        """
        return sorted(self._servers.keys())

    def get_all_configs(self) -> dict[str, ServerConfig]:
        """Get all registered configurations.

        Returns:
            Copy of the internal server configurations dictionary
        """
        return self._servers.copy()


# Global registry instance
registry = ServerRegistry()

# MCP Code Checker built-in config - COMPLETE PARAMETER SET
MCP_CODE_CHECKER = ServerConfig(
    name="mcp-code-checker",
    display_name="MCP Code Checker",
    main_module="src/main.py",
    parameters=[
        # Required parameters
        ParameterDef(
            name="project-dir",
            arg_name="--project-dir",
            param_type="path",
            required=True,
            help="Base directory for code checking operations (required)",
        ),
        # Python execution parameters
        ParameterDef(
            name="python-executable",
            arg_name="--python-executable",
            param_type="path",
            help="Path to Python interpreter to use for running tests. "
            "If not specified, defaults to the current Python interpreter (sys.executable)",
        ),
        ParameterDef(
            name="venv-path",
            arg_name="--venv-path",
            param_type="path",
            help="Path to virtual environment to activate for running tests. "
            "When specified, the Python executable from this venv will be used "
            "instead of python-executable",
        ),
        # Test configuration parameters
        ParameterDef(
            name="test-folder",
            arg_name="--test-folder",
            param_type="string",
            default="tests",
            help="Path to the test folder (relative to project_dir). Defaults to 'tests'",
        ),
        ParameterDef(
            name="keep-temp-files",
            arg_name="--keep-temp-files",
            param_type="boolean",
            is_flag=True,
            help="Keep temporary files after test execution. "
            "Useful for debugging when tests fail",
        ),
        # Logging parameters
        ParameterDef(
            name="log-level",
            arg_name="--log-level",
            param_type="choice",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set logging level (default: INFO)",
        ),
        ParameterDef(
            name="log-file",
            arg_name="--log-file",
            param_type="path",
            help="Path for structured JSON logs "
            "(default: mcp_code_checker_{timestamp}.log in project_dir/logs/)",
        ),
        ParameterDef(
            name="console-only",
            arg_name="--console-only",
            param_type="boolean",
            is_flag=True,
            help="Log only to console, ignore --log-file parameter",
        ),
    ],
)

# Register the built-in server
registry.register(MCP_CODE_CHECKER)
