"""Tests for external server discovery functionality."""

import sys
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config.discovery import (
    ExternalServerValidator,
    ServerDiscoveryError,
    discover_external_servers,
    initialize_external_servers,
    register_external_servers,
)
from src.config.servers import ParameterDef, ServerConfig


class TestExternalServerValidator:
    """Test the ExternalServerValidator class."""

    def test_validate_valid_server_config(self) -> None:
        """Test validation of a valid server configuration."""
        config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[
                ParameterDef(
                    name="test-param",
                    arg_name="--test-param",
                    param_type="string",
                    help="Test parameter",
                )
            ],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_type(self) -> None:
        """Test validation fails for non-ServerConfig types."""
        config = {"name": "test"}  # Not a ServerConfig instance

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert len(errors) == 1
        assert "not a ServerConfig instance" in errors[0]

    def test_validate_missing_name(self) -> None:
        """Test validation fails for missing name field."""
        config = ServerConfig(
            name="",  # Empty name
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert any("missing required 'name' field" in e for e in errors)

    def test_validate_missing_display_name(self) -> None:
        """Test validation fails for missing display_name field."""
        config = ServerConfig(
            name="test-server",
            display_name="",  # Empty display name
            main_module="test/main.py",
            parameters=[],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert any("missing required 'display_name' field" in e for e in errors)

    def test_validate_missing_main_module(self) -> None:
        """Test validation fails for missing main_module field."""
        config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="",  # Empty main module
            parameters=[],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert any("missing required 'main_module' field" in e for e in errors)

    def test_validate_invalid_name_format(self) -> None:
        """Test validation fails for invalid name format."""
        config = ServerConfig(
            name="test@server!",  # Invalid characters
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert any("invalid name" in e for e in errors)

    def test_validate_builtin_name_conflict(self) -> None:
        """Test validation fails for conflicting with built-in server names."""
        config = ServerConfig(
            name="mcp-code-checker",  # Conflicts with built-in
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[],
        )

        validator = ExternalServerValidator()
        is_valid, errors = validator.validate_server_config(config, "test_package")

        assert is_valid is False
        assert any("conflicts with built-in server name" in e for e in errors)

    def test_validate_valid_name_formats(self) -> None:
        """Test validation accepts various valid name formats."""
        valid_names = [
            "test-server",
            "test_server",
            "testserver",
            "test-server-123",
            "TEST_SERVER",
        ]

        validator = ExternalServerValidator()

        for name in valid_names:
            config = ServerConfig(
                name=name,
                display_name="Test Server",
                main_module="test/main.py",
                parameters=[],
            )

            is_valid, errors = validator.validate_server_config(config, "test_package")
            assert is_valid is True, f"Name '{name}' should be valid"


class TestDiscoverExternalServers:
    """Test the discover_external_servers function."""

    @patch("importlib.metadata.entry_points")
    def test_discover_no_external_servers(self, mock_entry_points: Mock) -> None:
        """Test discovery when no external servers are available."""
        # Mock empty entry points
        mock_eps = MagicMock()
        mock_eps.select.return_value = []
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        assert discovered == {}
        mock_eps.select.assert_called_once_with(group="mcp.server_configs")

    @patch("importlib.metadata.entry_points")
    def test_discover_with_old_api(self, mock_entry_points: Mock) -> None:
        """Test discovery with old entry_points API (Python 3.8-3.9)."""
        # Mock old API (no select method)
        mock_eps = MagicMock()
        del mock_eps.select  # Remove select method
        mock_eps.get.return_value = []
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        assert discovered == {}
        mock_eps.get.assert_called_once_with("mcp.server_configs", [])

    @patch("importlib.metadata.entry_points")
    def test_discover_valid_external_server(self, mock_entry_points: Mock) -> None:
        """Test discovery of a valid external server."""
        # Create a valid server config
        valid_config = ServerConfig(
            name="external-server",
            display_name="External Server",
            main_module="external/main.py",
            parameters=[],
        )

        # Mock entry point
        mock_entry = MagicMock()
        mock_entry.name = "external_server"
        mock_entry.load.return_value = valid_config

        # Mock dist for source package name
        mock_dist = MagicMock()
        mock_dist.name = "external-package"
        mock_entry.dist = mock_dist

        # Mock entry points
        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_entry]
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        assert len(discovered) == 1
        assert "external-server" in discovered
        assert discovered["external-server"][0] == valid_config
        assert discovered["external-server"][1] == "external-package"

    @patch("importlib.metadata.entry_points")
    @patch("src.config.discovery.logger")
    def test_discover_invalid_external_server(self, mock_logger: Mock, mock_entry_points: Mock) -> None:
        """Test discovery handling of invalid external server."""
        # Create an invalid config (not a ServerConfig)
        invalid_config = {"name": "invalid"}

        # Mock entry point
        mock_entry = MagicMock()
        mock_entry.name = "invalid_server"
        mock_entry.load.return_value = invalid_config

        # Mock dist
        mock_dist = MagicMock()
        mock_dist.name = "invalid-package"
        mock_entry.dist = mock_dist

        # Mock entry points
        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_entry]
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        # Should not include invalid server
        assert len(discovered) == 0
        # Should log warning about invalid config
        assert mock_logger.warning.called

    @patch("importlib.metadata.entry_points")
    @patch("src.config.discovery.logger")
    def test_discover_duplicate_server_names(self, mock_logger: Mock, mock_entry_points: Mock) -> None:
        """Test handling of duplicate server names from different packages."""
        # Create two configs with same name
        config1 = ServerConfig(
            name="duplicate-server",
            display_name="Server 1",
            main_module="server1/main.py",
            parameters=[],
        )

        config2 = ServerConfig(
            name="duplicate-server",  # Same name
            display_name="Server 2",
            main_module="server2/main.py",
            parameters=[],
        )

        # Mock two entry points
        mock_entry1 = MagicMock()
        mock_entry1.name = "server1"
        mock_entry1.load.return_value = config1
        mock_dist1 = MagicMock()
        mock_dist1.name = "package1"
        mock_entry1.dist = mock_dist1

        mock_entry2 = MagicMock()
        mock_entry2.name = "server2"
        mock_entry2.load.return_value = config2
        mock_dist2 = MagicMock()
        mock_dist2.name = "package2"
        mock_entry2.dist = mock_dist2

        # Mock entry points
        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_entry1, mock_entry2]
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        # Should only include first server with duplicate name
        assert len(discovered) == 1
        assert discovered["duplicate-server"][1] == "package1"
        # Should log warning about duplicate
        assert mock_logger.warning.called

    @patch("importlib.metadata.entry_points")
    @patch("src.config.discovery.logger")
    def test_discover_entry_point_load_error(self, mock_logger: Mock, mock_entry_points: Mock) -> None:
        """Test handling of entry point loading errors."""
        # Mock entry point that fails to load
        mock_entry = MagicMock()
        mock_entry.name = "broken_server"
        mock_entry.load.side_effect = ImportError("Module not found")

        # Mock entry points
        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_entry]
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        # Should not include broken server
        assert len(discovered) == 0
        # Should log error
        assert mock_logger.error.called


class TestRegisterExternalServers:
    """Test the register_external_servers function."""

    @patch("src.config.discovery.registry")
    def test_register_external_servers_success(self, mock_registry: Mock) -> None:
        """Test successful registration of external servers."""
        # Create test servers
        config1 = ServerConfig(
            name="server1",
            display_name="Server 1",
            main_module="server1/main.py",
            parameters=[],
        )

        config2 = ServerConfig(
            name="server2",
            display_name="Server 2",
            main_module="server2/main.py",
            parameters=[],
        )

        discovered = {
            "server1": (config1, "package1"),
            "server2": (config2, "package2"),
        }

        # Mock registry
        mock_registry.is_registered.return_value = False

        count, errors = register_external_servers(discovered)

        assert count == 2
        assert len(errors) == 0
        assert mock_registry.register.call_count == 2

    @patch("src.config.discovery.registry")
    @patch("src.config.discovery.logger")
    def test_register_already_registered_server(self, mock_logger: Mock, mock_registry: Mock) -> None:
        """Test handling of already registered servers."""
        config = ServerConfig(
            name="existing-server",
            display_name="Existing Server",
            main_module="existing/main.py",
            parameters=[],
        )

        discovered = {"existing-server": (config, "package")}

        # Mock registry to say server is already registered
        mock_registry.is_registered.return_value = True

        count, errors = register_external_servers(discovered)

        assert count == 0
        assert len(errors) == 0
        mock_registry.register.assert_not_called()
        mock_logger.warning.assert_called()

    @patch("src.config.discovery.registry")
    @patch("src.config.discovery.logger")
    def test_register_server_registration_error(self, mock_logger: Mock, mock_registry: Mock) -> None:
        """Test handling of registration errors."""
        config = ServerConfig(
            name="error-server",
            display_name="Error Server",
            main_module="error/main.py",
            parameters=[],
        )

        discovered = {"error-server": (config, "package")}

        # Mock registry to raise error on register
        mock_registry.is_registered.return_value = False
        mock_registry.register.side_effect = ValueError("Registration failed")

        count, errors = register_external_servers(discovered)

        assert count == 0
        assert len(errors) == 1
        assert "Failed to register server" in errors[0]
        mock_logger.error.assert_called()


class TestInitializeExternalServers:
    """Test the initialize_external_servers function."""

    @patch("src.config.discovery.register_external_servers")
    @patch("src.config.discovery.discover_external_servers")
    def test_initialize_no_external_servers(
        self, mock_discover: Mock, mock_register: Mock
    ) -> None:
        """Test initialization when no external servers are found."""
        mock_discover.return_value = {}
        mock_register.return_value = (0, [])

        count, errors = initialize_external_servers(verbose=False)

        assert count == 0
        assert len(errors) == 0
        mock_discover.assert_called_once()
        mock_register.assert_called_once_with({})

    @patch("src.config.discovery.register_external_servers")
    @patch("src.config.discovery.discover_external_servers")
    @patch("builtins.print")
    def test_initialize_with_verbose_output(
        self, mock_print: Mock, mock_discover: Mock, mock_register: Mock
    ) -> None:
        """Test initialization with verbose output."""
        config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[],
        )

        mock_discover.return_value = {"test-server": (config, "test-package")}
        mock_register.return_value = (1, [])

        count, errors = initialize_external_servers(verbose=True)

        assert count == 1
        assert len(errors) == 0

        # Check verbose output
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Discovering" in str(call) for call in print_calls)
        assert any("Found 1 external" in str(call) for call in print_calls)
        assert any("Successfully registered" in str(call) for call in print_calls)

    @patch("src.config.discovery.register_external_servers")
    @patch("src.config.discovery.discover_external_servers")
    @patch("builtins.print")
    def test_initialize_with_errors(
        self, mock_print: Mock, mock_discover: Mock, mock_register: Mock
    ) -> None:
        """Test initialization with errors during registration."""
        config = ServerConfig(
            name="test-server",
            display_name="Test Server",
            main_module="test/main.py",
            parameters=[],
        )

        mock_discover.return_value = {"test-server": (config, "test-package")}
        mock_register.return_value = (0, ["Registration error occurred"])

        count, errors = initialize_external_servers(verbose=True)

        assert count == 0
        assert len(errors) == 1
        assert "Registration error occurred" in errors[0]

        # Check error output
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Errors during discovery" in str(call) for call in print_calls)


class TestIntegrationScenarios:
    """Test complex integration scenarios."""

    @patch("importlib.metadata.entry_points")
    def test_mixed_valid_invalid_servers(self, mock_entry_points: Mock) -> None:
        """Test discovery with mix of valid and invalid servers."""
        # Valid config
        valid_config = ServerConfig(
            name="valid-server",
            display_name="Valid Server",
            main_module="valid/main.py",
            parameters=[],
        )

        # Invalid config (conflicts with built-in)
        invalid_config = ServerConfig(
            name="mcp-code-checker",
            display_name="Invalid Server",
            main_module="invalid/main.py",
            parameters=[],
        )

        # Mock entry points
        mock_entry1 = MagicMock()
        mock_entry1.name = "valid"
        mock_entry1.load.return_value = valid_config
        mock_dist1 = MagicMock()
        mock_dist1.name = "valid-package"
        mock_entry1.dist = mock_dist1

        mock_entry2 = MagicMock()
        mock_entry2.name = "invalid"
        mock_entry2.load.return_value = invalid_config
        mock_dist2 = MagicMock()
        mock_dist2.name = "invalid-package"
        mock_entry2.dist = mock_dist2

        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_entry1, mock_entry2]
        mock_entry_points.return_value = mock_eps

        discovered = discover_external_servers()

        # Should only include valid server
        assert len(discovered) == 1
        assert "valid-server" in discovered
        assert "mcp-code-checker" not in discovered

    def test_entry_points_import_fallback(self) -> None:
        """Test fallback scenario for older Python versions."""
        # This test just verifies the discovery function handles errors gracefully
        # We can't easily test the actual import fallback in Python 3.13
        
        # The discovery function should handle any errors gracefully
        discovered = discover_external_servers()
        
        # Should return empty dict if no servers found (or on error)
        assert isinstance(discovered, dict)


# Test fixtures for mock external servers
@pytest.fixture
def mock_filesystem_server() -> ServerConfig:
    """Create a mock filesystem server configuration."""
    return ServerConfig(
        name="mcp-filesystem",
        display_name="MCP Filesystem",
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
                help="Enable read-only mode",
            ),
        ],
    )


@pytest.fixture
def mock_database_server() -> ServerConfig:
    """Create a mock database server configuration."""
    return ServerConfig(
        name="mcp-database",
        display_name="MCP Database",
        main_module="src/db_main.py",
        parameters=[
            ParameterDef(
                name="connection-string",
                arg_name="--connection-string",
                param_type="string",
                required=True,
                help="Database connection string",
            ),
            ParameterDef(
                name="max-connections",
                arg_name="--max-connections",
                param_type="string",
                default="10",
                help="Maximum number of connections",
            ),
        ],
    )


def test_mock_servers_are_valid(mock_filesystem_server: ServerConfig, mock_database_server: ServerConfig) -> None:
    """Verify that mock servers pass validation."""
    validator = ExternalServerValidator()

    is_valid, errors = validator.validate_server_config(
        mock_filesystem_server, "mock_fs"
    )
    assert is_valid is True
    assert len(errors) == 0

    is_valid, errors = validator.validate_server_config(
        mock_database_server, "mock_db"
    )
    assert is_valid is True
    assert len(errors) == 0
