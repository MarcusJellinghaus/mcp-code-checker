"""Test API examples from documentation."""

import ast
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def test_api_serverconfig_example() -> None:
    """Test ServerConfig API example works."""
    from src.config.servers import ParameterDef, ServerConfig

    # Example from API.md
    config = ServerConfig(
        name="test-server",
        display_name="Test Server",
        main_module="src/main.py",
        parameters=[
            ParameterDef(
                name="test-param",
                arg_name="--test-param",
                param_type="string",
                required=True,
                help="Test parameter",
            )
        ],
    )

    assert config.name == "test-server"
    assert config.display_name == "Test Server"
    assert len(config.parameters) == 1
    assert config.parameters[0].name == "test-param"


def test_api_parameterdef_example() -> None:
    """Test ParameterDef API example works."""
    from src.config.servers import ParameterDef

    # Example from API.md
    param = ParameterDef(
        name="param-name",
        arg_name="--param-name",
        param_type="string",
        required=False,
        default=None,
        choices=None,
        help="Parameter description",
        is_flag=False,
    )

    assert param.name == "param-name"
    assert param.arg_name == "--param-name"
    assert param.param_type == "string"
    assert not param.required


def test_api_registry_example() -> None:
    """Test ServerRegistry API example works."""
    from src.config.servers import ParameterDef, ServerConfig, ServerRegistry

    # Create a test registry
    registry = ServerRegistry()

    # Create and register a server config
    config = ServerConfig(
        name="test-api-server",
        display_name="Test API Server",
        main_module="test.py",
        parameters=[],
    )

    registry.register(config)

    # Test retrieval
    retrieved = registry.get("test-api-server")
    assert retrieved is not None
    assert retrieved.name == "test-api-server"

    # Test listing
    servers = registry.list_servers()
    assert "test-api-server" in servers


def test_generate_args_example() -> None:
    """Test generate_args method example."""
    from src.config.servers import ParameterDef, ServerConfig

    config = ServerConfig(
        name="example-server",
        display_name="Example Server",
        main_module="main.py",
        parameters=[
            ParameterDef(
                name="input-file",
                arg_name="--input",
                param_type="path",
                required=True,
                help="Input file path",
            ),
            ParameterDef(
                name="verbose",
                arg_name="--verbose",
                param_type="boolean",
                is_flag=True,
                help="Enable verbose output",
            ),
        ],
    )

    # Note: generate_args expects underscored parameter names
    user_params = {"input_file": "/path/to/file.txt", "verbose": True}

    args = config.generate_args(user_params)

    assert "main.py" in args
    assert "--input" in args
    assert "/path/to/file.txt" in args
    assert "--verbose" in args


def test_required_params_example() -> None:
    """Test get_required_params method example."""
    from src.config.servers import ParameterDef, ServerConfig

    config = ServerConfig(
        name="test-server",
        display_name="Test",
        main_module="main.py",
        parameters=[
            ParameterDef(
                name="required-param",
                arg_name="--required",
                param_type="string",
                required=True,
                help="Required parameter",
            ),
            ParameterDef(
                name="optional-param",
                arg_name="--optional",
                param_type="string",
                required=False,
                help="Optional parameter",
            ),
        ],
    )

    required = config.get_required_params()
    assert "required-param" in required
    assert "optional-param" not in required
    assert len(required) == 1


@patch("src.config.clients.get_client_handler")
def test_client_handler_example(mock_get_client: Mock) -> None:
    """Test ClientHandler API example."""
    # Mock the handler instance
    mock_handler = Mock()
    mock_get_client.return_value = mock_handler

    # Import after patching
    from src.config.clients import get_client_handler

    # Example from API.md
    handler = get_client_handler("claude-desktop")

    # Test that methods can be called
    mock_handler.setup_server.return_value = True
    mock_handler.remove_server.return_value = True
    mock_handler.list_managed_servers.return_value = []

    result = handler.setup_server("test", {})
    assert mock_handler.setup_server.called

    result = handler.remove_server("test")
    assert mock_handler.remove_server.called

    servers = handler.list_managed_servers()
    assert mock_handler.list_managed_servers.called


def test_validation_pattern_example() -> None:
    """Test validation pattern from API documentation."""
    from pathlib import Path

    from src.config.servers import ParameterDef, ServerConfig, ServerRegistry

    def setup_server_safely(
        server_type: str, name: str, params: dict[str, str]
    ) -> list[str]:
        """Setup server with comprehensive error handling (from API.md)."""

        # Create a test registry with a test server
        registry = ServerRegistry()
        test_config = ServerConfig(
            name="test-type",
            display_name="Test",
            main_module="main.py",
            parameters=[
                ParameterDef(
                    name="project-dir",
                    arg_name="--project-dir",
                    param_type="path",
                    required=True,
                    help="Project directory",
                )
            ],
        )
        registry.register(test_config)

        # Validate server type
        server_config = registry.get(server_type)
        if not server_config:
            available = registry.list_servers()
            raise ValueError(
                f"Unknown server type '{server_type}'. Available: {available}"
            )

        # Validate required parameters
        required = server_config.get_required_params()
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Validate project directory if specified
        project_dir = params.get("project-dir")
        if project_dir:
            project_path = Path(project_dir)
            if not project_path.exists():
                raise ValueError(f"Project directory does not exist: {project_dir}")

            if not server_config.validate_project(project_path):
                raise ValueError(
                    f"Project directory is not compatible with {server_type}"
                )

        # Generate configuration
        args = server_config.generate_args(params)
        return args

    # Test with valid parameters
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create required structure
        project_path = Path(tmpdir)
        (project_path / "src").mkdir()
        (project_path / "src" / "main.py").touch()

        params = {"project-dir": tmpdir}
        args = setup_server_safely("test-type", "test-name", params)
        assert "main.py" in args

    # Test with missing parameters
    with pytest.raises(ValueError, match="Missing required parameters"):
        setup_server_safely("test-type", "test-name", {})

    # Test with unknown server type
    with pytest.raises(ValueError, match="Unknown server type"):
        setup_server_safely("unknown-type", "test-name", {})


def test_external_server_config_example() -> None:
    """Test external server configuration example from INTEGRATION.md."""
    from src.config.servers import ParameterDef, ServerConfig

    # Filesystem server example from INTEGRATION.md
    FILESYSTEM_CONFIG = ServerConfig(
        name="mcp-filesystem",
        display_name="MCP Filesystem Server",
        main_module="src/main.py",
        parameters=[
            ParameterDef(
                name="root-dir",
                arg_name="--root-dir",
                param_type="path",
                required=True,
                help="Root directory for filesystem access",
            ),
            ParameterDef(
                name="read-only",
                arg_name="--read-only",
                param_type="boolean",
                is_flag=True,
                help="Enable read-only mode (no write operations)",
            ),
            ParameterDef(
                name="max-file-size",
                arg_name="--max-file-size",
                param_type="string",
                default="10MB",
                help="Maximum file size to read (e.g., '10MB', '1GB')",
            ),
            ParameterDef(
                name="log-level",
                arg_name="--log-level",
                param_type="choice",
                choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                default="INFO",
                help="Set logging level",
            ),
        ],
    )

    # Test the configuration
    assert FILESYSTEM_CONFIG.name == "mcp-filesystem"
    assert len(FILESYSTEM_CONFIG.parameters) == 4

    # Test required parameters
    required = FILESYSTEM_CONFIG.get_required_params()
    assert "root-dir" in required
    assert "read-only" not in required

    # Test argument generation
    # Note: generate_args expects underscored parameter names
    user_params = {
        "root_dir": "/home/user/docs",
        "read_only": True,
        "log_level": "DEBUG",
    }

    args = FILESYSTEM_CONFIG.generate_args(user_params)
    assert "src/main.py" in args
    assert "--root-dir" in args
    assert "/home/user/docs" in args
    assert "--read-only" in args
    assert "--log-level" in args
    assert "DEBUG" in args


def test_parameter_types_examples() -> None:
    """Test all parameter type examples from INTEGRATION.md."""
    from src.config.servers import ParameterDef

    # String parameter
    string_param = ParameterDef(
        name="connection-string",
        arg_name="--connection-string",
        param_type="string",
        required=True,
        help="Database connection string",
    )
    assert string_param.param_type == "string"

    # Path parameter
    path_param = ParameterDef(
        name="root-directory",
        arg_name="--root-dir",
        param_type="path",
        required=True,
        help="Root directory for file operations",
    )
    assert path_param.param_type == "path"

    # Boolean flag
    bool_param = ParameterDef(
        name="read-only",
        arg_name="--read-only",
        param_type="boolean",
        is_flag=True,
        help="Enable read-only mode",
    )
    assert bool_param.is_flag

    # Choice parameter
    choice_param = ParameterDef(
        name="log-level",
        arg_name="--log-level",
        param_type="choice",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )
    assert choice_param.param_type == "choice"
    assert choice_param.choices == ["DEBUG", "INFO", "WARNING", "ERROR"]

    # Optional parameter with default
    optional_param = ParameterDef(
        name="timeout",
        arg_name="--timeout",
        param_type="string",
        default="30s",
        help="Request timeout duration",
    )
    assert optional_param.default == "30s"
    assert not optional_param.required
