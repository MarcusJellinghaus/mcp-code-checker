"""Tests for CLI utilities module."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.cli_utils import (
    add_parameter_to_parser,
    build_setup_parser,
    create_full_parser,
    get_list_examples,
    get_remove_examples,
    get_setup_examples,
    get_usage_examples,
    parse_and_validate_args,
    validate_list_args,
    validate_remove_args,
    validate_setup_args,
)
from src.config.servers import ParameterDef, ServerConfig, registry


class TestParserBuilding:
    """Test parser building functions."""

    def test_build_setup_parser(self) -> None:
        """Test building setup command parser."""
        parser = build_setup_parser("mcp-code-checker")

        # Parse basic valid args
        args = parser.parse_args(
            ["mcp-code-checker", "test-server", "--project-dir", "."]
        )
        assert args.server_type == "mcp-code-checker"
        assert args.server_name == "test-server"
        assert args.project_dir == Path(".")

    def test_create_full_parser(self) -> None:
        """Test creating full parser with all commands."""
        parser = create_full_parser()

        # Test setup command
        args = parser.parse_args(
            ["setup", "mcp-code-checker", "test", "--project-dir", "."]
        )
        assert args.command == "setup"
        assert args.server_type == "mcp-code-checker"

        # Test remove command
        args = parser.parse_args(["remove", "test-server"])
        assert args.command == "remove"
        assert args.server_name == "test-server"

        # Test list command
        args = parser.parse_args(["list", "--detailed"])
        assert args.command == "list"
        assert args.detailed is True

    def test_add_parameter_to_parser(self) -> None:
        """Test adding individual parameters to parser."""
        parser = argparse.ArgumentParser()

        # String parameter
        param = ParameterDef(
            name="test-string",
            arg_name="--test-string",
            param_type="string",
            help="Test string parameter",
            default="default_value",
        )
        add_parameter_to_parser(parser, param)

        # Boolean flag
        param = ParameterDef(
            name="test-flag",
            arg_name="--test-flag",
            param_type="boolean",
            is_flag=True,
            help="Test flag",
        )
        add_parameter_to_parser(parser, param)

        # Choice parameter
        param = ParameterDef(
            name="log-level",
            arg_name="--log-level",
            param_type="choice",
            choices=["DEBUG", "INFO", "WARNING"],
            help="Log level",
        )
        add_parameter_to_parser(parser, param)

        # Path parameter
        param = ParameterDef(
            name="project-dir",
            arg_name="--project-dir",
            param_type="path",
            required=True,
            help="Project directory",
        )
        add_parameter_to_parser(parser, param)

        # Parse test args
        args = parser.parse_args(
            [
                "--test-string",
                "custom",
                "--test-flag",
                "--log-level",
                "DEBUG",
                "--project-dir",
                "/path/to/project",
            ]
        )
        assert args.test_string == "custom"
        assert args.test_flag is True
        assert args.log_level == "DEBUG"
        assert args.project_dir == Path("/path/to/project")


class TestParameterHandling:
    """Test parameter-specific functionality."""

    def test_all_mcp_code_checker_parameters(self) -> None:
        """Test that all 8 MCP Code Checker parameters are supported."""
        parser = build_setup_parser("mcp-code-checker")

        # Parse with all parameters
        args = parser.parse_args(
            [
                "mcp-code-checker",
                "test",
                "--project-dir",
                ".",
                "--python-executable",
                "/usr/bin/python3",
                "--venv-path",
                ".venv",
                "--test-folder",
                "tests",
                "--keep-temp-files",
                "--log-level",
                "DEBUG",
                "--log-file",
                "test.log",
                "--console-only",
            ]
        )

        assert args.project_dir == Path(".")
        assert args.python_executable == Path("/usr/bin/python3")
        assert args.venv_path == Path(".venv")
        assert args.test_folder == "tests"
        assert args.keep_temp_files is True
        assert args.log_level == "DEBUG"
        assert args.log_file == Path("test.log")
        assert args.console_only is True

    def test_required_parameters(self) -> None:
        """Test that required parameters are enforced."""
        parser = build_setup_parser("mcp-code-checker")

        # Should fail without required --project-dir
        with pytest.raises(SystemExit):
            parser.parse_args(["mcp-code-checker", "test"])

    def test_default_values(self) -> None:
        """Test that default values are applied."""
        parser = build_setup_parser("mcp-code-checker")

        # Parse with minimal args
        args = parser.parse_args(["mcp-code-checker", "test", "--project-dir", "."])

        # Check defaults
        assert args.test_folder == "tests"  # Default value
        assert args.log_level == "INFO"  # Default value
        assert args.keep_temp_files is False  # Default for flags
        assert args.console_only is False  # Default for flags

    def test_choice_validation(self) -> None:
        """Test that choice parameters are validated."""
        parser = build_setup_parser("mcp-code-checker")

        # Valid choice
        args = parser.parse_args(
            ["mcp-code-checker", "test", "--project-dir", ".", "--log-level", "DEBUG"]
        )
        assert args.log_level == "DEBUG"

        # Invalid choice should fail
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "mcp-code-checker",
                    "test",
                    "--project-dir",
                    ".",
                    "--log-level",
                    "INVALID",
                ]
            )


class TestValidation:
    """Test argument validation functions."""

    def test_validate_setup_args(self) -> None:
        """Test setup argument validation."""
        # Create mock args
        args = MagicMock()
        args.server_type = "mcp-code-checker"
        args.project_dir = Path(".")

        # Valid args
        errors = validate_setup_args(args)
        assert errors == []

        # Invalid server type
        args.server_type = "invalid-server"
        errors = validate_setup_args(args)
        assert len(errors) > 0
        assert "Unknown server type" in errors[0]

    def test_validate_remove_args(self) -> None:
        """Test remove argument validation."""
        # Valid args
        args = MagicMock()
        args.server_name = "test-server"
        errors = validate_remove_args(args)
        assert errors == []

        # Missing server name
        args.server_name = ""
        errors = validate_remove_args(args)
        assert len(errors) == 1
        assert "Server name is required" in errors[0]

    def test_validate_list_args(self) -> None:
        """Test list argument validation."""
        # List command has no required validation
        args = MagicMock()
        errors = validate_list_args(args)
        assert errors == []

    def test_parse_and_validate_args(self) -> None:
        """Test combined parsing and validation."""
        # Valid setup command
        args, errors = parse_and_validate_args(
            ["setup", "mcp-code-checker", "test", "--project-dir", "."]
        )
        assert args.command == "setup"
        assert len(errors) == 0

        # Valid remove command
        args, errors = parse_and_validate_args(["remove", "test-server"])
        assert args.command == "remove"
        assert len(errors) == 0

        # Valid list command
        args, errors = parse_and_validate_args(["list"])
        assert args.command == "list"
        assert len(errors) == 0


class TestHelpText:
    """Test help text generation."""

    def test_get_usage_examples(self) -> None:
        """Test main usage examples."""
        examples = get_usage_examples()
        assert "mcp-config setup" in examples
        assert "mcp-config remove" in examples
        assert "mcp-config list" in examples
        assert "--project-dir" in examples

    def test_get_setup_examples(self) -> None:
        """Test setup command examples."""
        examples = get_setup_examples()
        assert "auto-detection" in examples
        assert "--log-level DEBUG" in examples
        assert "--python-executable" in examples
        assert "--venv-path" in examples
        assert "--console-only" in examples
        assert "--dry-run" in examples

    def test_get_remove_examples(self) -> None:
        """Test remove command examples."""
        examples = get_remove_examples()
        assert "mcp-config remove" in examples
        assert "--dry-run" in examples
        assert "--no-backup" in examples

    def test_get_list_examples(self) -> None:
        """Test list command examples."""
        examples = get_list_examples()
        assert "mcp-config list" in examples
        assert "--detailed" in examples
        assert "--managed-only" in examples


class TestAutoDetectionIntegration:
    """Test auto-detection integration in CLI."""

    def test_auto_detect_hints_in_help(self) -> None:
        """Test that auto-detection is mentioned in help text."""
        parser = build_setup_parser("mcp-code-checker")
        help_text = parser.format_help()

        # Check that auto-detected parameters mention it
        assert "auto-detect" in help_text.lower()

    def test_parameter_with_auto_detect(self) -> None:
        """Test parameters with auto-detect flag."""
        param = ParameterDef(
            name="test-param",
            arg_name="--test-param",
            param_type="path",
            auto_detect=True,
            help="Test parameter",
        )

        parser = argparse.ArgumentParser()
        add_parameter_to_parser(parser, param)

        # Help should mention auto-detection
        help_text = parser.format_help()
        assert "auto-detected if not specified" in help_text


class TestGlobalOptions:
    """Test global CLI options."""

    def test_global_options_in_all_commands(self) -> None:
        """Test that global options are available in all commands."""
        parser = create_full_parser()

        # Setup command with global options
        args = parser.parse_args(
            [
                "setup",
                "mcp-code-checker",
                "test",
                "--project-dir",
                ".",
                "--dry-run",
                "--verbose",
                "--no-backup",
            ]
        )
        assert args.dry_run is True
        assert args.verbose is True
        assert args.backup is False

        # Remove command with global options
        args = parser.parse_args(
            [
                "remove",
                "test",
                "--dry-run",
                "--verbose",
            ]
        )
        assert args.dry_run is True
        assert args.verbose is True

        # List command with its options
        args = parser.parse_args(
            [
                "list",
                "--detailed",
                "--managed-only",
            ]
        )
        assert args.detailed is True
        assert args.managed_only is True


class TestDynamicServerRegistration:
    """Test dynamic server registration in CLI."""

    def test_registered_servers_in_choices(self) -> None:
        """Test that registered servers appear in CLI choices."""
        parser = create_full_parser()

        # MCP Code Checker should be in choices
        help_text = parser.format_help()
        assert "mcp-code-checker" in help_text

        # Should be able to parse it
        args = parser.parse_args(
            ["setup", "mcp-code-checker", "test", "--project-dir", "."]
        )
        assert args.server_type == "mcp-code-checker"

    @patch.object(registry, "list_servers")
    def test_multiple_servers(self, mock_list_servers: MagicMock) -> None:
        """Test CLI with multiple registered servers."""
        # Mock multiple servers
        mock_list_servers.return_value = ["mcp-code-checker", "another-server"]

        parser = create_full_parser()
        help_text = parser.format_help()

        # Both servers should be mentioned
        assert "mcp-code-checker" in help_text
