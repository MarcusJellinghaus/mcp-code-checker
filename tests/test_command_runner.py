"""Tests for the command runner utilities."""

import sys
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch

import pytest

from src.utils.command_runner import (
    CommandOptions,
    CommandResult,
    CommandRunner,
    CommandRunnerFactory,
    CommandRunnerType,
    SubprocessCommandRunner,
    execute_command,
    execute_subprocess_with_timeout,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def reset_factory() -> Generator[None, None, None]:
    """Reset the CommandRunnerFactory after each test."""
    yield
    CommandRunnerFactory.reset()


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_creation(self) -> None:
        """Test creating a CommandResult instance."""
        result = CommandResult(
            return_code=0,
            stdout="output",
            stderr="",
            timed_out=False,
            execution_error=None,
            command=["echo", "test"],
            runner_type="subprocess",
            execution_time_ms=100,
        )

        assert result.return_code == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert not result.timed_out
        assert result.execution_error is None
        assert result.command == ["echo", "test"]
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms == 100

    def test_command_result_defaults(self) -> None:
        """Test CommandResult with minimal required fields."""
        result = CommandResult(
            return_code=1,
            stdout="",
            stderr="error",
            timed_out=True,
        )

        assert result.return_code == 1
        assert result.stdout == ""
        assert result.stderr == "error"
        assert result.timed_out
        assert result.execution_error is None
        assert result.command is None
        assert result.runner_type is None
        assert result.execution_time_ms is None


class TestCommandOptions:
    """Tests for CommandOptions dataclass."""

    def test_command_options_defaults(self) -> None:
        """Test CommandOptions with default values."""
        options = CommandOptions()

        assert options.cwd is None
        assert options.timeout_seconds == 120
        assert options.env is None
        assert options.capture_output is True
        assert options.text is True
        assert not options.check
        assert not options.shell
        assert options.input_data is None

    def test_command_options_custom(self) -> None:
        """Test CommandOptions with custom values."""
        options = CommandOptions(
            cwd="/tmp",
            timeout_seconds=60,
            env={"TEST": "value"},
            capture_output=False,
            text=False,
            check=True,
            shell=True,
            input_data="test input",
        )

        assert options.cwd == "/tmp"
        assert options.timeout_seconds == 60
        assert options.env == {"TEST": "value"}
        assert not options.capture_output
        assert not options.text
        assert options.check
        assert options.shell
        assert options.input_data == "test input"


class TestSubprocessCommandRunner:
    """Tests for SubprocessCommandRunner."""

    def test_subprocess_runner_creation(self) -> None:
        """Test creating a SubprocessCommandRunner."""
        runner = SubprocessCommandRunner()
        assert runner.name == "subprocess"
        assert runner.is_available()

    def test_execute_simple_command(self) -> None:
        """Test executing a simple command."""
        runner = SubprocessCommandRunner()
        result = runner.execute([sys.executable, "-c", "print('hello')"])

        assert result.return_code == 0
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert not result.timed_out
        assert result.execution_error is None
        assert result.command == [sys.executable, "-c", "print('hello')"]
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

    def test_execute_command_with_options(self, temp_dir: Path) -> None:
        """Test executing a command with custom options."""
        runner = SubprocessCommandRunner()
        options = CommandOptions(
            cwd=str(temp_dir),
            timeout_seconds=30,
            env={"TEST_VAR": "test_value"},
        )

        result = runner.execute(
            [
                sys.executable,
                "-c",
                "import os; print(os.environ.get('TEST_VAR', 'NOT_FOUND'))",
            ],
            options,
        )

        assert result.return_code == 0
        assert "test_value" in result.stdout
        assert result.command is not None
        assert result.runner_type == "subprocess"

    def test_execute_command_with_error(self) -> None:
        """Test executing a command that returns an error."""
        runner = SubprocessCommandRunner()
        result = runner.execute([sys.executable, "-c", "import sys; sys.exit(1)"])

        assert result.return_code == 1
        assert not result.timed_out
        assert result.execution_error is None
        assert result.runner_type == "subprocess"

    def test_execute_command_not_found(self) -> None:
        """Test executing a command that doesn't exist."""
        runner = SubprocessCommandRunner()
        result = runner.execute(["nonexistent_command_12345"])

        assert result.return_code == 1
        assert result.timed_out is False
        assert result.execution_error is not None
        assert "Executable not found" in result.execution_error
        assert result.runner_type == "subprocess"

    def test_execute_command_timeout(self) -> None:
        """Test executing a command that times out."""
        runner = SubprocessCommandRunner()
        options = CommandOptions(timeout_seconds=1)

        result = runner.execute(
            [sys.executable, "-c", "import time; time.sleep(5)"], options
        )

        assert result.return_code == 1
        assert result.timed_out is True
        assert result.execution_error is not None
        assert "Process timed out after 1 seconds" in result.execution_error
        assert result.runner_type == "subprocess"

    def test_execute_command_permission_error(self) -> None:
        """Test handling permission errors."""
        runner = SubprocessCommandRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = PermissionError("Access denied")

            result = runner.execute(["test_command"])

            assert result.return_code == 1
            assert not result.timed_out
            assert result.execution_error is not None
            assert "Permission error" in result.execution_error
            assert result.runner_type == "subprocess"

    def test_execute_command_unexpected_error(self) -> None:
        """Test handling unexpected errors."""
        runner = SubprocessCommandRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Unexpected error")

            result = runner.execute(["test_command"])

            assert result.return_code == 1
            assert not result.timed_out
            assert result.execution_error is not None
            assert "Unexpected error" in result.execution_error
            assert result.runner_type == "subprocess"


class TestCommandRunnerFactory:
    """Tests for CommandRunnerFactory."""

    def test_get_default_runner(self, reset_factory: Any) -> None:
        """Test getting the default runner."""
        runner = CommandRunnerFactory.get_runner()
        assert isinstance(runner, SubprocessCommandRunner)
        assert runner.name == "subprocess"

    def test_get_subprocess_runner(self, reset_factory: Any) -> None:
        """Test explicitly getting subprocess runner."""
        runner = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)
        assert isinstance(runner, SubprocessCommandRunner)
        assert runner.name == "subprocess"

    def test_get_unavailable_runner_falls_back(self, reset_factory: Any) -> None:
        """Test that unavailable runners fall back to subprocess."""
        # Try to get a runner that's not implemented yet
        runner = CommandRunnerFactory.get_runner(CommandRunnerType.PLUMBUM)

        # Should fall back to subprocess
        assert isinstance(runner, SubprocessCommandRunner)
        assert runner.name == "subprocess"

    def test_set_default_runner(self, reset_factory: Any) -> None:
        """Test setting a different default runner."""
        CommandRunnerFactory.set_default_runner(CommandRunnerType.PLUMBUM)

        # Should still get subprocess due to fallback
        runner = CommandRunnerFactory.get_runner()
        assert isinstance(runner, SubprocessCommandRunner)

    def test_get_available_runners(self, reset_factory: Any) -> None:
        """Test getting list of available runners."""
        available = CommandRunnerFactory.get_available_runners()

        assert CommandRunnerType.SUBPROCESS in available
        # Other runners should not be available yet
        assert len(available) == 1

    def test_register_custom_runner(self, reset_factory: Any) -> None:
        """Test registering a custom runner."""

        class MockRunner(CommandRunner):
            def __init__(self) -> None:
                super().__init__("mock")

            def execute(self, command: Any, options: Any = None) -> CommandResult:
                return CommandResult(
                    return_code=0,
                    stdout="mock output",
                    stderr="",
                    timed_out=False,
                    runner_type=self.name,
                )

            def is_available(self) -> bool:
                return True

        mock_runner = MockRunner()
        CommandRunnerFactory.register_runner(CommandRunnerType.PLUMBUM, mock_runner)

        runner = CommandRunnerFactory.get_runner(CommandRunnerType.PLUMBUM)
        assert runner.name == "mock"
        assert isinstance(runner, MockRunner)

    def test_factory_caches_runners(self, reset_factory: Any) -> None:
        """Test that factory caches runner instances."""
        runner1 = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)
        runner2 = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)

        # Should be the same instance
        assert runner1 is runner2

    def test_reset_factory(self, reset_factory: Any) -> None:
        """Test resetting the factory."""
        # Get a runner to populate the cache
        runner1 = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)

        # Reset the factory
        CommandRunnerFactory.reset()

        # Get another runner
        runner2 = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)

        # Should be different instances
        assert runner1 is not runner2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_execute_command(self) -> None:
        """Test the execute_command convenience function."""
        result = execute_command([sys.executable, "-c", "print('test')"])

        assert result.return_code == 0
        assert "test" in result.stdout
        assert result.runner_type == "subprocess"

    def test_execute_command_with_options(self, temp_dir: Path) -> None:
        """Test execute_command with custom options."""
        result = execute_command(
            [sys.executable, "-c", "import os; print(os.getcwd())"],
            cwd=str(temp_dir),
            timeout_seconds=30,
        )

        assert result.return_code == 0
        assert str(temp_dir) in result.stdout
        assert result.runner_type == "subprocess"

    def test_execute_command_with_runner_type(self) -> None:
        """Test execute_command with explicit runner type."""
        result = execute_command(
            [sys.executable, "-c", "print('test')"],
            runner_type=CommandRunnerType.SUBPROCESS,
        )

        assert result.return_code == 0
        assert "test" in result.stdout
        assert result.runner_type == "subprocess"

    def test_execute_subprocess_with_timeout_backward_compatibility(self) -> None:
        """Test backward compatibility function."""
        result = execute_subprocess_with_timeout(
            [sys.executable, "-c", "print('backward compatible')"]
        )

        assert result.return_code == 0
        assert "backward compatible" in result.stdout
        assert result.runner_type == "subprocess"

        # Should be compatible with old SubprocessResult
        assert hasattr(result, "return_code")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "timed_out")
        assert hasattr(result, "execution_error")

    def test_execute_subprocess_with_timeout_all_params(self, temp_dir: Path) -> None:
        """Test backward compatibility function with all parameters."""
        result = execute_subprocess_with_timeout(
            command=[sys.executable, "-c", "import os; print(os.getcwd())"],
            cwd=str(temp_dir),
            timeout_seconds=60,
            env={"TEST": "value"},
        )

        assert result.return_code == 0
        assert str(temp_dir) in result.stdout
        assert result.runner_type == "subprocess"


class TestCommandRunnerType:
    """Tests for CommandRunnerType enum."""

    def test_enum_values(self) -> None:
        """Test that enum values are correct."""
        assert CommandRunnerType.SUBPROCESS.value == "subprocess"
        assert CommandRunnerType.PLUMBUM.value == "plumbum"
        assert CommandRunnerType.SH.value == "sh"
        assert CommandRunnerType.INVOKE.value == "invoke"

    def test_enum_iteration(self) -> None:
        """Test iterating over enum values."""
        values = [runner_type.value for runner_type in CommandRunnerType]
        expected = ["subprocess", "plumbum", "sh", "invoke"]
        assert values == expected


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_empty_command_list(self) -> None:
        """Test handling of empty command list."""
        runner = SubprocessCommandRunner()
        result = runner.execute([])

        assert result.return_code == 1
        assert result.execution_error is not None
        assert result.runner_type == "subprocess"

    def test_none_command(self) -> None:
        """Test handling of None command."""
        runner = SubprocessCommandRunner()

        with pytest.raises(TypeError):
            runner.execute(None)  # type: ignore[arg-type]

    def test_invalid_options(self) -> None:
        """Test handling of invalid options."""
        runner = SubprocessCommandRunner()

        # This should work - None options should use defaults
        result = runner.execute([sys.executable, "-c", "print('test')"], None)
        assert result.return_code == 0


class TestIntegrationWithExistingCode:
    """Integration tests to ensure compatibility with existing code."""

    def test_subprocess_result_alias(self) -> None:
        """Test that SubprocessResult is aliased correctly."""
        from src.utils.command_runner import CommandResult, SubprocessResult

        # Should be the same class
        assert SubprocessResult is CommandResult

    def test_result_structure_compatibility(self) -> None:
        """Test that result structure is compatible with existing code."""
        result = execute_subprocess_with_timeout(
            [sys.executable, "-c", "print('test')"]
        )

        # Test that all expected attributes exist and have correct types
        assert isinstance(result.return_code, int)
        assert isinstance(result.stdout, str)
        assert isinstance(result.stderr, str)
        assert isinstance(result.timed_out, bool)
        assert result.execution_error is None or isinstance(result.execution_error, str)

        # Test new attributes
        assert result.command is None or isinstance(result.command, list)
        assert result.runner_type is None or isinstance(result.runner_type, str)
        assert result.execution_time_ms is None or isinstance(
            result.execution_time_ms, int
        )

    def test_logging_integration(self) -> None:
        """Test that logging decorators work correctly."""
        # The @log_function_call decorator should work without issues
        result = execute_subprocess_with_timeout(
            [sys.executable, "-c", "print('logging test')"]
        )

        assert result.return_code == 0
        assert "logging test" in result.stdout


@pytest.fixture
def mock_runner() -> Generator[CommandRunner, None, None]:
    """Create a mock runner for testing."""

    class MockRunner(CommandRunner):
        def __init__(self) -> None:
            super().__init__("mock")

        def execute(self, command: Any, options: Any = None) -> CommandResult:
            return CommandResult(
                return_code=0,
                stdout="mock output",
                stderr="",
                timed_out=False,
                runner_type=self.name,
            )

        def is_available(self) -> bool:
            return True

    yield MockRunner()


@pytest.fixture
def subprocess_runner() -> SubprocessCommandRunner:
    """Create a SubprocessCommandRunner for testing."""
    return SubprocessCommandRunner()


@pytest.fixture
def sample_command() -> list[str]:
    """Sample command for testing."""
    return [sys.executable, "-c", "print('test')"]


@pytest.fixture
def sample_command_options() -> CommandOptions:
    """Sample command options for testing."""
    return CommandOptions(
        cwd=None,
        timeout_seconds=30,
        env={"TEST": "value"},
    )


@pytest.fixture
def sample_command_result() -> CommandResult:
    """Sample command result for testing."""
    return CommandResult(
        return_code=0,
        stdout="test output",
        stderr="",
        timed_out=False,
        command=["echo", "test"],
        runner_type="subprocess",
        execution_time_ms=100,
    )


def test_command_result_creation_with_fixture(
    sample_command_result: CommandResult,
) -> None:
    """Test command result creation using fixture."""
    assert sample_command_result.return_code == 0
    assert sample_command_result.stdout == "test output"
    assert sample_command_result.runner_type == "subprocess"


def test_subprocess_runner_with_fixture(
    subprocess_runner: SubprocessCommandRunner,
) -> None:
    """Test subprocess runner using fixture."""
    assert subprocess_runner.name == "subprocess"
    assert subprocess_runner.is_available()


def test_sample_command_with_fixture(sample_command: list[str]) -> None:
    """Test sample command fixture."""
    assert len(sample_command) == 3
    assert sample_command[0] == sys.executable


def test_command_options_with_fixture(sample_command_options: CommandOptions) -> None:
    """Test command options fixture."""
    assert sample_command_options.timeout_seconds == 30
    assert sample_command_options.env is not None
    assert sample_command_options.env["TEST"] == "value"


def test_mock_runner_with_fixture(mock_runner: CommandRunner) -> None:
    """Test mock runner fixture."""
    result = mock_runner.execute(["test"])
    assert result.return_code == 0
    assert result.stdout == "mock output"


def test_execution_with_timeout_custom() -> None:
    """Test execution with custom timeout."""
    runner = SubprocessCommandRunner()
    options = CommandOptions(timeout_seconds=5)

    result = runner.execute([sys.executable, "-c", "print('timeout test')"], options)
    assert result.return_code == 0
    assert "timeout test" in result.stdout


def test_execution_with_env_vars() -> None:
    """Test execution with environment variables."""
    runner = SubprocessCommandRunner()
    options = CommandOptions(env={"CUSTOM_VAR": "custom_value"})

    result = runner.execute(
        [
            sys.executable,
            "-c",
            "import os; print(os.environ.get('CUSTOM_VAR', 'NOT_SET'))",
        ],
        options,
    )

    assert result.return_code == 0
    assert "custom_value" in result.stdout


def test_execution_time_tracking() -> None:
    """Test that execution time is tracked."""
    runner = SubprocessCommandRunner()
    result = runner.execute([sys.executable, "-c", "import time; time.sleep(0.1)"])

    assert result.execution_time_ms is not None
    assert result.execution_time_ms >= 100  # At least 100ms due to sleep


def test_command_factory_singleton_behavior() -> None:
    """Test factory singleton behavior."""
    CommandRunnerFactory.reset()

    runner1 = CommandRunnerFactory.get_runner()
    runner2 = CommandRunnerFactory.get_runner()

    assert runner1 is runner2


def test_backwards_compatibility_complete() -> None:
    """Test complete backwards compatibility with original interface."""
    # This should work exactly like the old function
    result = execute_subprocess_with_timeout([sys.executable, "--version"])

    # All original attributes should exist
    assert hasattr(result, "return_code")
    assert hasattr(result, "stdout")
    assert hasattr(result, "stderr")
    assert hasattr(result, "timed_out")
    assert hasattr(result, "execution_error")

    # New attributes should also be present
    assert hasattr(result, "command")
    assert hasattr(result, "runner_type")
    assert hasattr(result, "execution_time_ms")


def test_error_handling_comprehensive() -> None:
    """Test comprehensive error handling."""
    runner = SubprocessCommandRunner()

    # Test file not found
    result = runner.execute(["this_command_does_not_exist_12345"])
    assert result.return_code == 1
    assert result.execution_error is not None
    assert "Executable not found" in result.execution_error

    # Test with proper command that should work
    result = runner.execute([sys.executable, "-c", "print('success')"])
    assert result.return_code == 0
    assert result.execution_error is None
