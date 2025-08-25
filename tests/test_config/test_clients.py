"""Tests for client handlers."""

import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Type
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.config.clients import ClaudeDesktopHandler, get_client_handler


def mock_path_for_platform(base_path: str) -> Type[Any]:
    """Create a mock Path that works across platforms for testing."""

    class MockPath:
        def __init__(self, *parts: str) -> None:
            if parts and isinstance(parts[0], str):
                self._path = parts[0]
            else:
                self._path = str(base_path)
            for part in parts[1:]:
                self._path = self._path + "/" + str(part)

        def __truediv__(self, other: str) -> "MockPath":
            return MockPath(self._path + "/" + str(other))

        def __str__(self) -> str:
            return self._path

        @property
        def name(self) -> str:
            return self._path.split("/")[-1]

        @classmethod
        def home(cls) -> "MockPath":
            return cls(base_path)

    return MockPath


class TestClaudeDesktopHandler:
    """Test ClaudeDesktopHandler functionality."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def handler(self, temp_config_dir: Path, monkeypatch: Any) -> ClaudeDesktopHandler:
        """Create a handler with mocked config path."""
        handler = ClaudeDesktopHandler()
        config_path = temp_config_dir / "claude_desktop_config.json"
        monkeypatch.setattr(handler, "get_config_path", lambda: config_path)
        return handler

    @pytest.fixture
    def sample_config(self) -> Dict[str, Any]:
        """Sample Claude Desktop configuration."""
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "node",
                    "args": ["filesystem-server.js"],
                },
                "calculator": {
                    "command": "python",
                    "args": ["calculator.py"],
                    "env": {"PYTHONPATH": "/path/to/lib"},
                },
            }
        }

    @pytest.fixture
    def managed_server_config(self) -> Dict[str, Any]:
        """Configuration for a managed server."""
        return {
            "command": "/usr/bin/python",
            "args": ["src/main.py", "--project-dir", "/test/project"],
            "env": {"PYTHONPATH": "/test/project"},
            "_managed_by": "mcp-config-managed",
            "_server_type": "mcp-code-checker",
        }

    def test_config_path_windows(self) -> None:
        """Test Windows config path detection."""
        handler = ClaudeDesktopHandler()

        # Create a proper mock class for Windows Path
        class MockWindowsPath:
            def __init__(self, path: str = "C:\\Users\\TestUser") -> None:
                self._path = path

            def __str__(self) -> str:
                return self._path

            def __truediv__(self, other: str) -> "MockWindowsPath":
                return MockWindowsPath(f"{self._path}\\{other}")

            @property
            def name(self) -> str:
                return self._path.split("\\")[-1]

        mock_home = MockWindowsPath()

        with patch("os.name", "nt"), patch("pathlib.Path.home", return_value=mock_home):
            path = handler.get_config_path()
            path_str = str(path).replace("\\", "/")
            assert "AppData" in path_str
            assert "Roaming" in path_str
            assert "Claude" in path_str
            assert path.name == "claude_desktop_config.json"

    def test_config_path_macos(self) -> None:
        """Test macOS config path detection."""
        handler = ClaudeDesktopHandler()

        MockPath = mock_path_for_platform("/Users/TestUser")
        mock_home = MockPath()

        with (
            patch("os.name", "posix"),
            patch("platform.system", return_value="Darwin"),
            patch("pathlib.Path.home", return_value=mock_home),
            patch("src.config.clients.Path", MockPath),
        ):
            path = handler.get_config_path()
            path_str = str(path)
            assert "Library" in path_str
            assert "Application Support" in path_str
            assert "Claude" in path_str
            assert path.name == "claude_desktop_config.json"

    def test_config_path_linux(self) -> None:
        """Test Linux config path detection."""
        handler = ClaudeDesktopHandler()

        MockPath = mock_path_for_platform("/home/testuser")
        mock_home = MockPath()

        with (
            patch("os.name", "posix"),
            patch("platform.system", return_value="Linux"),
            patch("pathlib.Path.home", return_value=mock_home),
            patch("src.config.clients.Path", MockPath),
        ):
            path = handler.get_config_path()
            path_str = str(path)
            assert ".config" in path_str
            assert "claude" in path_str
            assert path.name == "claude_desktop_config.json"

    def test_load_missing_config(self, handler: ClaudeDesktopHandler) -> None:
        """Test loading when config doesn't exist."""
        config = handler.load_config()
        assert config == {"mcpServers": {}}

    def test_load_existing_config(
        self, handler: ClaudeDesktopHandler, sample_config: Dict[str, Any]
    ) -> None:
        """Test loading existing configuration."""
        config_path = handler.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(sample_config, f)

        loaded = handler.load_config()
        assert loaded == sample_config
        assert "filesystem" in loaded["mcpServers"]
        assert "calculator" in loaded["mcpServers"]

    def test_load_config_missing_mcp_servers(
        self, handler: ClaudeDesktopHandler
    ) -> None:
        """Test loading config without mcpServers section."""
        config_path = handler.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({"otherSection": {}}, f)

        loaded = handler.load_config()
        assert "mcpServers" in loaded
        assert loaded["mcpServers"] == {}

    def test_save_config_creates_directories(
        self, handler: ClaudeDesktopHandler
    ) -> None:
        """Test that save creates parent directories."""
        config = {"mcpServers": {"test": {"command": "test"}}}
        config_path = handler.get_config_path()

        assert not config_path.exists()
        handler.save_config(config)

        assert config_path.exists()
        with open(config_path) as f:
            saved = json.load(f)
        assert saved == config

    def test_save_config_atomic_write(
        self, handler: ClaudeDesktopHandler, sample_config: Dict[str, Any]
    ) -> None:
        """Test atomic write behavior."""
        # Save initial config
        handler.save_config(sample_config)
        config_path = handler.get_config_path()

        # Verify no .tmp file remains
        temp_files = list(config_path.parent.glob("*.tmp"))
        assert len(temp_files) == 0

        # Verify content is correct
        with open(config_path) as f:
            saved = json.load(f)
        assert saved == sample_config

    def test_setup_server_preserves_external(
        self,
        handler: ClaudeDesktopHandler,
        sample_config: Dict[str, Any],
        managed_server_config: Dict[str, Any],
    ) -> None:
        """Test that setup_server preserves external servers."""
        # Save initial config with external servers
        handler.save_config(sample_config)

        # Add a managed server
        success = handler.setup_server("my-checker", managed_server_config)
        assert success

        # Load and verify
        config = handler.load_config()
        assert "filesystem" in config["mcpServers"]  # External preserved
        assert "calculator" in config["mcpServers"]  # External preserved
        assert "my-checker" in config["mcpServers"]  # New managed server

        # Check managed server has markers
        checker_config = config["mcpServers"]["my-checker"]
        assert checker_config["_managed_by"] == "mcp-config-managed"
        assert checker_config["_server_type"] == "mcp-code-checker"

    def test_setup_server_update_existing(
        self, handler: ClaudeDesktopHandler, managed_server_config: Dict[str, Any]
    ) -> None:
        """Test updating an existing managed server."""
        # Set up initial server
        handler.setup_server("test-server", managed_server_config)

        # Update with new configuration
        updated_config = managed_server_config.copy()
        updated_config["args"] = ["src/main.py", "--project-dir", "/new/path"]

        success = handler.setup_server("test-server", updated_config)
        assert success

        # Verify update
        config = handler.load_config()
        assert "/new/path" in config["mcpServers"]["test-server"]["args"]

    def test_remove_managed_server(
        self, handler: ClaudeDesktopHandler, managed_server_config: Dict[str, Any]
    ) -> None:
        """Test removing a managed server."""
        # Set up a server
        handler.setup_server("test-server", managed_server_config)

        # Remove it
        success = handler.remove_server("test-server")
        assert success

        # Verify it's gone
        config = handler.load_config()
        assert "test-server" not in config["mcpServers"]

    def test_remove_external_server_fails(
        self, handler: ClaudeDesktopHandler, sample_config: Dict[str, Any]
    ) -> None:
        """Test that removing external servers fails."""
        handler.save_config(sample_config)

        # Try to remove external server
        success = handler.remove_server("filesystem")
        assert not success  # Should fail

        # Verify it's still there
        config = handler.load_config()
        assert "filesystem" in config["mcpServers"]

    def test_remove_nonexistent_server(self, handler: ClaudeDesktopHandler) -> None:
        """Test removing a server that doesn't exist."""
        success = handler.remove_server("nonexistent")
        assert not success

    def test_list_managed_servers(
        self,
        handler: ClaudeDesktopHandler,
        sample_config: Dict[str, Any],
        managed_server_config: Dict[str, Any],
    ) -> None:
        """Test listing only managed servers."""
        handler.save_config(sample_config)
        handler.setup_server("managed-1", managed_server_config)
        handler.setup_server("managed-2", managed_server_config)

        managed = handler.list_managed_servers()
        assert len(managed) == 2

        names = [s["name"] for s in managed]
        assert "managed-1" in names
        assert "managed-2" in names
        assert "filesystem" not in names  # External not included

    def test_list_all_servers(
        self,
        handler: ClaudeDesktopHandler,
        sample_config: Dict[str, Any],
        managed_server_config: Dict[str, Any],
    ) -> None:
        """Test listing all servers with management status."""
        handler.save_config(sample_config)
        handler.setup_server("managed-1", managed_server_config)

        all_servers = handler.list_all_servers()
        assert len(all_servers) == 3

        # Check management status
        server_map = {s["name"]: s for s in all_servers}
        assert server_map["filesystem"]["managed"] is False
        assert server_map["calculator"]["managed"] is False
        assert server_map["managed-1"]["managed"] is True

    def test_backup_config(
        self, handler: ClaudeDesktopHandler, sample_config: Dict[str, Any]
    ) -> None:
        """Test configuration backup."""
        handler.save_config(sample_config)

        backup_path = handler.backup_config()
        assert backup_path.exists()
        assert "backup" in backup_path.name
        assert backup_path.suffix == ".json"

        # Verify backup content
        with open(backup_path) as f:
            backup_content = json.load(f)
        assert backup_content == sample_config

    def test_backup_missing_config(self, handler: ClaudeDesktopHandler) -> None:
        """Test backup when config doesn't exist."""
        backup_path = handler.backup_config()
        # Should return the config path but not create a backup
        assert backup_path == handler.get_config_path()

    def test_validate_config_valid(
        self, handler: ClaudeDesktopHandler, sample_config: Dict[str, Any]
    ) -> None:
        """Test validation of valid configuration."""
        handler.save_config(sample_config)
        errors = handler.validate_config()
        assert len(errors) == 0

    def test_validate_config_missing_command(
        self, handler: ClaudeDesktopHandler
    ) -> None:
        """Test validation catches missing command."""
        bad_config = {
            "mcpServers": {
                "bad-server": {
                    "args": ["test.py"],  # Missing command
                }
            }
        }
        handler.save_config(bad_config)
        errors = handler.validate_config()
        assert len(errors) > 0
        assert any("command" in e for e in errors)

    def test_validate_config_invalid_args_type(
        self, handler: ClaudeDesktopHandler
    ) -> None:
        """Test validation catches invalid args type."""
        bad_config = {
            "mcpServers": {
                "bad-server": {
                    "command": "python",
                    "args": "should-be-list",  # Wrong type
                }
            }
        }
        handler.save_config(bad_config)
        errors = handler.validate_config()
        assert len(errors) > 0
        assert any("args" in e and "array" in e for e in errors)

    def test_validate_config_invalid_env_type(
        self, handler: ClaudeDesktopHandler
    ) -> None:
        """Test validation catches invalid env type."""
        bad_config = {
            "mcpServers": {
                "bad-server": {
                    "command": "python",
                    "env": ["should", "be", "dict"],  # Wrong type
                }
            }
        }
        handler.save_config(bad_config)
        errors = handler.validate_config()
        assert len(errors) > 0
        assert any("env" in e and "object" in e for e in errors)


class TestClientRegistry:
    """Test client registry functionality."""

    def test_get_client_handler_valid(self) -> None:
        """Test getting a valid client handler."""
        handler = get_client_handler("claude-desktop")
        assert isinstance(handler, ClaudeDesktopHandler)

    def test_get_client_handler_invalid(self) -> None:
        """Test getting an invalid client handler."""
        with pytest.raises(ValueError) as exc_info:
            get_client_handler("invalid-client")
        assert "Unknown client" in str(exc_info.value)
        assert "claude-desktop" in str(exc_info.value)

    def test_registry_contains_claude_desktop(self) -> None:
        """Test that claude-desktop is in the registry."""
        from src.config.clients import CLIENT_HANDLERS

        assert "claude-desktop" in CLIENT_HANDLERS
        assert CLIENT_HANDLERS["claude-desktop"] == ClaudeDesktopHandler
