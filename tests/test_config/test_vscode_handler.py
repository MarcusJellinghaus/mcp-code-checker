"""Tests for VSCode MCP configuration handler."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config.clients import VSCodeHandler


class TestVSCodeHandler:
    """Test VSCode handler functionality."""

    def test_workspace_config_path(self) -> None:
        """Test workspace configuration path."""
        handler = VSCodeHandler(workspace=True)

        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/home/user/project")
            config_path = handler.get_config_path()

            assert config_path == Path("/home/user/project/.vscode/mcp.json")

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Linux-specific path handling cannot be tested on Windows",
    )
    def test_user_config_path_linux(self):
        """Test user profile configuration path on Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch.object(os, "name", "posix"):
                handler = VSCodeHandler(workspace=False)

                # Just check that the path contains expected components
                config_path = handler.get_config_path()
                path_str = str(config_path)

                assert ".config" in path_str
                assert "Code" in path_str
                assert "mcp.json" in path_str

    def test_user_config_path_windows(self):
        """Test user profile configuration path on Windows."""
        handler = VSCodeHandler(workspace=False)

        with patch("os.name", "nt"):
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path("C:/Users/TestUser")
                config_path = handler.get_config_path()

                # Check string representation for cross-platform compatibility
                assert "AppData" in str(config_path)
                assert "Code" in str(config_path)
                assert "mcp.json" in str(config_path)

    @pytest.mark.skipif(
        os.name == "nt",
        reason="macOS-specific path handling cannot be tested on Windows",
    )
    def test_user_config_path_macos(self):
        """Test user profile configuration path on macOS."""
        with patch("platform.system", return_value="Darwin"):
            with patch.object(os, "name", "posix"):
                handler = VSCodeHandler(workspace=False)

                config_path = handler.get_config_path()
                path_str = str(config_path)

                # Check for macOS-specific path components
                assert (
                    "Library" in path_str
                    or "Application Support" in path_str.replace("\\", "/")
                )
                assert "Code" in path_str
                assert "mcp.json" in path_str

    def test_setup_server(self, tmp_path):
        """Test setting up a server configuration."""
        # Create handler with temp workspace
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Setup server
            server_config = {
                "command": "python",
                "args": ["-m", "mcp_code_checker", "--project-dir", "/path/to/project"],
                "env": {"PYTHONPATH": "/path/to/project"},
                "_server_type": "mcp-code-checker",
            }

            result = handler.setup_server("test-server", server_config)
            assert result is True

            # Check configuration was saved
            config_path = tmp_path / ".vscode" / "mcp.json"
            assert config_path.exists()

            with open(config_path) as f:
                config = json.load(f)

            assert "servers" in config
            assert "test-server" in config["servers"]
            assert config["servers"]["test-server"]["command"] == "python"
            assert config["servers"]["test-server"]["args"][0] == "-m"

            # Check metadata was saved
            metadata_path = tmp_path / ".vscode" / ".mcp-config-metadata.json"
            assert metadata_path.exists()

            with open(metadata_path) as f:
                metadata = json.load(f)

            assert "test-server" in metadata
            assert metadata["test-server"]["_managed_by"] == "mcp-config-managed"

    def test_remove_managed_server(self, tmp_path):
        """Test removing a managed server."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Setup initial config
            config = {
                "servers": {
                    "managed-server": {
                        "command": "python",
                        "args": ["-m", "mcp_code_checker"],
                    },
                    "external-server": {"command": "node", "args": ["server.js"]},
                }
            }

            # Setup metadata (only managed-server is tracked)
            metadata = {
                "managed-server": {
                    "_managed_by": "mcp-config-managed",
                    "_server_type": "mcp-code-checker",
                }
            }

            # Save config and metadata
            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)

            with open(config_path / ".mcp-config-metadata.json", "w") as f:
                json.dump(metadata, f)

            # Remove managed server
            result = handler.remove_server("managed-server")
            assert result is True

            # Check it was removed
            with open(config_path / "mcp.json") as f:
                updated_config = json.load(f)

            assert "managed-server" not in updated_config["servers"]
            assert "external-server" in updated_config["servers"]  # External preserved

            # Try to remove external server (should fail)
            result = handler.remove_server("external-server")
            assert result is False

    def test_list_servers(self, tmp_path):
        """Test listing all servers."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Setup config with mixed servers
            config = {
                "servers": {
                    "managed1": {"command": "python", "args": []},
                    "external1": {"command": "node", "args": []},
                    "managed2": {"command": "python", "args": []},
                }
            }

            metadata = {
                "managed1": {
                    "_managed_by": "mcp-config-managed",
                    "_server_type": "mcp-code-checker",
                },
                "managed2": {
                    "_managed_by": "mcp-config-managed",
                    "_server_type": "mcp-code-checker",
                },
            }

            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)

            with open(config_path / ".mcp-config-metadata.json", "w") as f:
                json.dump(metadata, f)

            # List all servers
            all_servers = handler.list_all_servers()
            assert len(all_servers) == 3

            managed_count = sum(1 for s in all_servers if s["managed"])
            assert managed_count == 2

            # List managed only
            managed_servers = handler.list_managed_servers()
            assert len(managed_servers) == 2
            assert all(s["name"] in ["managed1", "managed2"] for s in managed_servers)

    def test_validate_config(self, tmp_path):
        """Test configuration validation."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Test with invalid config
            config = {
                "servers": {
                    "invalid-server": {
                        # Missing required 'command' field
                        "args": []
                    }
                }
            }

            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)

            errors = handler.validate_config()
            assert len(errors) > 0
            assert any(
                "missing required 'command' field" in e.lower()
                or "command" in e.lower()
                for e in errors
            )

    def test_backup_config(self, tmp_path):
        """Test configuration backup."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Create initial config
            config = {"servers": {"test": {"command": "python", "args": []}}}
            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)

            # Create backup
            backup_path = handler.backup_config()

            assert backup_path.exists()
            assert backup_path.name.startswith("mcp_backup_")
            assert backup_path.suffix == ".json"

            # Verify backup content
            with open(backup_path) as f:
                backup_content = json.load(f)

            assert backup_content == config

    def test_empty_config_handling(self, tmp_path):
        """Test handling of empty configuration."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # List servers when no config exists
            servers = handler.list_all_servers()
            assert len(servers) == 0

            # Validate when no config exists (should be valid)
            errors = handler.validate_config()
            assert len(errors) == 0

    def test_malformed_json_handling(self, tmp_path):
        """Test handling of malformed JSON configuration."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Create malformed JSON
            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                f.write("{ invalid json }")

            # load_config should handle gracefully and return default config
            config: dict[str, dict[str, dict]] = handler.load_config()
            assert config == {"servers": {}}  # Should return default config

            # List operations should work even with malformed JSON
            servers = handler.list_all_servers()
            assert len(servers) == 0  # No servers in default config

    def test_workspace_vs_user_distinction(self):
        """Test that workspace and user handlers are distinct."""
        workspace_handler = VSCodeHandler(workspace=True)
        user_handler = VSCodeHandler(workspace=False)

        assert workspace_handler.workspace is True
        assert user_handler.workspace is False

        # Config paths should be different
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/home/user/project")
            with patch("pathlib.Path.home") as mock_home:
                mock_home.return_value = Path("/home/user")
                with patch("platform.system") as mock_system:
                    mock_system.return_value = "Linux"

                    workspace_path = workspace_handler.get_config_path()
                    user_path = user_handler.get_config_path()

                    assert workspace_path != user_path
                    assert ".vscode" in str(workspace_path)
                    assert ".config" in str(user_path) or "AppData" in str(user_path)
