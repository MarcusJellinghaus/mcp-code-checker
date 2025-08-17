"""
Tests for subprocess STDIO fix and enhanced command runner.
"""

import os
import queue
import subprocess
import sys
import threading
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.command_runner import (
    CommandOptions,
    CommandResult,
    CommandRunnerFactory,
    CommandRunnerType,
    SubprocessCommandRunner,
    execute_command,
    execute_subprocess_with_timeout,
)
from src.utils.subprocess_stdio_fix import SubprocessSTDIOFix


class TestSubprocessSTDIOFix:
    """Test cases for SubprocessSTDIOFix class."""

    def test_get_isolated_environment(self) -> None:
        """Test environment isolation setup."""
        env = SubprocessSTDIOFix.get_isolated_environment()

        # Check critical environment variables are set
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["PYTHONDONTWRITEBYTECODE"] == "1"
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONNOUSERSITE"] == "1"
        assert env["PYTHONHASHSEED"] == "0"
        assert env["PYTHONSTARTUP"] == ""

        # Check MCP variables are removed
        mcp_vars = ["MCP_STDIO_TRANSPORT", "MCP_SERVER_NAME", "MCP_CLIENT_PARAMS"]
        for var in mcp_vars:
            assert var not in env

    def test_is_python_command_detection(self) -> None:
        """Test Python command detection."""
        # Python commands that should be detected
        python_commands = [
            ["python", "script.py"],
            ["python3", "-u", "script.py"],
            ["python.exe", "script.py"],
            [sys.executable, "script.py"],
            ["python", "-m", "module"],
            ["python3", "-m", "pytest"],
        ]

        for cmd in python_commands:
            assert SubprocessSTDIOFix.is_python_command(
                cmd
            ), f"Failed to detect Python command: {cmd}"

        # Non-Python commands that should not be detected
        non_python_commands = [
            ["echo", "hello"],
            ["node", "script.js"],
            ["java", "-jar", "app.jar"],
            ["cmd", "/c", "dir"],
            [],
        ]

        for cmd in non_python_commands:
            assert not SubprocessSTDIOFix.is_python_command(
                cmd
            ), f"Incorrectly detected as Python: {cmd}"

    def test_execute_with_stdio_isolation_success(self, tmp_path: Path) -> None:
        """Test successful Python subprocess execution with STDIO isolation."""
        # Create test script
        test_script = tmp_path / "test_script.py"
        test_script.write_text(
            "import sys\n"
            "print('Hello from subprocess')\n"
            "print('Args:', sys.argv[1:])\n"
            "sys.exit(0)\n"
        )

        command = [sys.executable, "-u", str(test_script), "arg1", "arg2"]

        result = SubprocessSTDIOFix.execute_with_stdio_isolation(
            command=command, cwd=str(tmp_path), timeout=5.0
        )

        assert result.returncode == 0
        assert "Hello from subprocess" in result.stdout
        assert "Args: ['arg1', 'arg2']" in result.stdout
        assert result.stderr == ""

    def test_execute_with_stdio_isolation_with_error(self, tmp_path: Path) -> None:
        """Test Python subprocess that writes to stderr."""
        test_script = tmp_path / "error_script.py"
        test_script.write_text(
            "import sys\n"
            "print('Normal output')\n"
            "print('Error message', file=sys.stderr)\n"
            "sys.exit(1)\n"
        )

        command = [sys.executable, "-u", str(test_script)]

        result = SubprocessSTDIOFix.execute_with_stdio_isolation(
            command=command, cwd=str(tmp_path), timeout=5.0
        )

        assert result.returncode == 1
        assert "Normal output" in result.stdout
        assert "Error message" in result.stderr

    def test_execute_with_stdio_isolation_timeout(self, tmp_path: Path) -> None:
        """Test subprocess timeout handling."""
        test_script = tmp_path / "timeout_script.py"
        test_script.write_text(
            "import time\n" "time.sleep(10)\n" "print('Should not reach here')\n"
        )

        command = [sys.executable, "-u", str(test_script)]

        with pytest.raises(subprocess.TimeoutExpired):
            SubprocessSTDIOFix.execute_with_stdio_isolation(
                command=command, cwd=str(tmp_path), timeout=1.0
            )

    def test_execute_regular_subprocess(self) -> None:
        """Test regular subprocess execution for non-Python commands."""
        if os.name == "nt":  # Windows
            command = ["cmd", "/c", "echo hello"]
        else:  # Unix/Linux
            command = ["echo", "hello"]

        result = SubprocessSTDIOFix.execute_regular_subprocess(
            command=command, timeout=5.0
        )

        assert result.returncode == 0
        assert "hello" in result.stdout.strip()

    def test_environment_mcp_variables_removed(self) -> None:
        """Test that MCP environment variables are properly removed."""
        # Set some fake MCP environment variables
        original_env = os.environ.copy()

        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "test_transport"
            os.environ["MCP_SERVER_NAME"] = "test_server"
            os.environ["MCP_CLIENT_PARAMS"] = "test_params"

            env = SubprocessSTDIOFix.get_isolated_environment()

            assert "MCP_STDIO_TRANSPORT" not in env
            assert "MCP_SERVER_NAME" not in env
            assert "MCP_CLIENT_PARAMS" not in env

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_environment_merging(self, tmp_path: Path) -> None:
        """Test that provided environment variables are merged with isolation settings."""
        test_script = tmp_path / "env_test.py"
        test_script.write_text(
            "import os\n"
            "print('CUSTOM_VAR:', os.environ.get('CUSTOM_VAR', 'NOT_SET'))\n"
            "print('PYTHONUNBUFFERED:', os.environ.get('PYTHONUNBUFFERED', 'NOT_SET'))\n"
        )

        command = [sys.executable, "-u", str(test_script)]
        custom_env = {"CUSTOM_VAR": "test_value"}

        result = SubprocessSTDIOFix.execute_with_stdio_isolation(
            command=command, cwd=str(tmp_path), timeout=5.0, env=custom_env
        )

        assert result.returncode == 0
        assert "CUSTOM_VAR: test_value" in result.stdout
        assert "PYTHONUNBUFFERED: 1" in result.stdout


class TestEnhancedCommandRunner:
    """Test cases for the enhanced command runner with STDIO isolation."""

    def test_subprocess_command_runner_python_detection(self) -> None:
        """Test that SubprocessCommandRunner correctly detects Python commands."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            runner = SubprocessCommandRunner()

        with (
            patch(
                "src.utils.subprocess_runner.execute_with_stdio_isolation"
            ) as mock_isolated,
            patch(
                "src.utils.subprocess_runner.execute_regular_subprocess"
            ) as mock_regular,
        ):

            # Setup mocks
            mock_result = subprocess.CompletedProcess(
                args=["python", "test.py"],
                returncode=0,
                stdout="test output",
                stderr="",
            )
            mock_isolated.return_value = mock_result
            mock_regular.return_value = mock_result

            # Test Python command
            python_command = ["python", "test.py"]
            options = CommandOptions(timeout_seconds=5)

            result = runner.execute(python_command, options)

            # Should use STDIO isolation
            mock_isolated.assert_called_once()
            mock_regular.assert_not_called()
            assert result.return_code == 0

    def test_subprocess_command_runner_non_python_command(self) -> None:
        """Test that SubprocessCommandRunner uses regular execution for non-Python commands."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            runner = SubprocessCommandRunner()

        with (
            patch(
                "src.utils.subprocess_runner.execute_with_stdio_isolation"
            ) as mock_isolated,
            patch(
                "src.utils.subprocess_runner.execute_regular_subprocess"
            ) as mock_regular,
        ):

            # Setup mock
            mock_result = subprocess.CompletedProcess(
                args=["echo", "test"], returncode=0, stdout="test", stderr=""
            )
            mock_regular.return_value = mock_result

            # Test non-Python command
            echo_command = ["echo", "test"]
            options = CommandOptions(timeout_seconds=5)

            result = runner.execute(echo_command, options)

            # Should use regular subprocess
            mock_regular.assert_called_once()
            mock_isolated.assert_not_called()
            assert result.return_code == 0

    def test_command_runner_factory_subprocess_creation(self) -> None:
        """Test CommandRunnerFactory creates subprocess runner correctly."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # Reset factory state
            CommandRunnerFactory.reset()

            runner = CommandRunnerFactory.get_runner(CommandRunnerType.SUBPROCESS)

        assert isinstance(runner, SubprocessCommandRunner)
        assert runner.is_available()

    def test_execute_command_convenience_function_python(self, tmp_path: Path) -> None:
        """Test execute_command convenience function with Python command."""
        test_script = tmp_path / "convenience_test.py"
        test_script.write_text("print('Convenience test')\n")

        command = [sys.executable, "-u", str(test_script)]

        result = execute_command(command=command, cwd=str(tmp_path), timeout_seconds=5)

        assert result.return_code == 0
        assert "Convenience test" in result.stdout

    def test_execute_subprocess_with_timeout_backward_compatibility(
        self, tmp_path: Path
    ) -> None:
        """Test backward compatibility function."""
        test_script = tmp_path / "compat_test.py"
        test_script.write_text("print('Backward compatibility test')\n")

        command = [sys.executable, "-u", str(test_script)]

        result = execute_subprocess_with_timeout(
            command=command, cwd=str(tmp_path), timeout_seconds=5
        )

        assert result.return_code == 0
        assert "Backward compatibility test" in result.stdout

    def test_command_runner_timeout_handling(self, tmp_path: Path) -> None:
        """Test timeout handling in command runner."""
        test_script = tmp_path / "timeout_test.py"
        test_script.write_text(
            "import time\n" "time.sleep(10)\n" "print('Should not reach here')\n"
        )

        command = [sys.executable, "-u", str(test_script)]

        result = execute_command(command=command, cwd=str(tmp_path), timeout_seconds=1)

        assert result.return_code == 1
        assert result.timed_out is True
        assert (
            result.execution_error is not None and "timed out" in result.execution_error
        )

    def test_command_runner_error_handling(self) -> None:
        """Test error handling in command runner."""
        # Test with non-existent executable
        command = ["nonexistent_executable", "arg"]

        result = execute_command(command=command, timeout_seconds=5)

        assert result.return_code == 1
        assert result.timed_out is False
        assert (
            result.execution_error is not None
            and "not found" in result.execution_error.lower()
        )

    def test_command_options_validation(self) -> None:
        """Test CommandOptions dataclass."""
        options = CommandOptions(
            cwd="/tmp",
            timeout_seconds=30,
            env={"TEST": "value"},
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            input_data="test input",
        )

        assert options.cwd == "/tmp"
        assert options.timeout_seconds == 30
        assert options.env is not None and options.env["TEST"] == "value"
        assert options.capture_output is True
        assert options.text is True
        assert options.check is False
        assert options.shell is False
        assert options.input_data == "test input"


class TestIntegrationScenarios:
    """Integration tests simulating real MCP server scenarios."""

    def test_multiple_sequential_python_commands(self, tmp_path: Path) -> None:
        """Test multiple sequential Python commands with STDIO isolation."""
        # Create multiple test scripts
        scripts = []
        for i in range(3):
            script = tmp_path / f"script_{i}.py"
            script.write_text(f"print('Script {i} output')\n")
            scripts.append(script)

        results = []
        for script in scripts:
            command = [sys.executable, "-u", str(script)]
            result = execute_command(
                command=command, cwd=str(tmp_path), timeout_seconds=5
            )
            results.append(result)

        # All should succeed
        for i, result in enumerate(results):
            assert result.return_code == 0
            assert f"Script {i} output" in result.stdout

    def test_mixed_command_types_sequential(self, tmp_path: Path) -> None:
        """Test mixed Python and non-Python commands in sequence."""
        # Create Python script
        python_script = tmp_path / "python_test.py"
        python_script.write_text("print('Python output')\n")

        commands = [
            [sys.executable, "-u", str(python_script)],  # Python command
        ]

        # Add platform-specific non-Python command
        if os.name == "nt":  # Windows
            commands.append(["cmd", "/c", "echo Non-Python output"])
        else:  # Unix/Linux
            commands.append(["echo", "Non-Python output"])

        results = []
        for command in commands:
            result = execute_command(
                command=command, cwd=str(tmp_path), timeout_seconds=5
            )
            results.append(result)

        # All should succeed
        assert len(results) == 2
        assert results[0].return_code == 0
        assert "Python output" in results[0].stdout
        assert results[1].return_code == 0
        assert "Non-Python output" in results[1].stdout

    def test_concurrent_subprocess_simulation(self, tmp_path: Path) -> None:
        """Test behavior under concurrent subprocess scenarios."""

        test_script = tmp_path / "concurrent_test.py"
        test_script.write_text(
            "import time\n"
            "import sys\n"
            "thread_id = sys.argv[1]\n"
            "print(f'Thread {thread_id} started')\n"
            "time.sleep(0.1)\n"
            "print(f'Thread {thread_id} finished')\n"
        )

        results_queue: queue.Queue[tuple[int, CommandResult | Exception]] = (
            queue.Queue()
        )

        def run_subprocess(thread_id: int) -> None:
            try:
                command = [sys.executable, "-u", str(test_script), str(thread_id)]
                result = execute_command(
                    command=command, cwd=str(tmp_path), timeout_seconds=5
                )
                results_queue.put((thread_id, result))
            except Exception as e:
                results_queue.put((thread_id, e))

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_subprocess, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == 3
        for thread_id, result in results:
            assert isinstance(result, CommandResult)
            assert result.return_code == 0
            assert f"Thread {thread_id} started" in result.stdout
            assert f"Thread {thread_id} finished" in result.stdout

    def test_environment_variable_isolation_integration(self, tmp_path: Path) -> None:
        """Test that environment variable isolation works in integration scenarios."""
        # Set up some environment variables that could interfere
        original_env = os.environ.copy()

        try:
            os.environ["MCP_STDIO_TRANSPORT"] = "test_transport"
            os.environ["CUSTOM_TEST_VAR"] = "should_be_preserved"

            test_script = tmp_path / "env_isolation_test.py"
            test_script.write_text(
                "import os\n"
                "mcp_var = os.environ.get('MCP_STDIO_TRANSPORT', 'NOT_SET')\n"
                "custom_var = os.environ.get('CUSTOM_TEST_VAR', 'NOT_SET')\n"
                "python_var = os.environ.get('PYTHONUNBUFFERED', 'NOT_SET')\n"
                "print(f'MCP_STDIO_TRANSPORT: {mcp_var}')\n"
                "print(f'CUSTOM_TEST_VAR: {custom_var}')\n"
                "print(f'PYTHONUNBUFFERED: {python_var}')\n"
            )

            command = [sys.executable, "-u", str(test_script)]

            result = execute_command(
                command=command,
                cwd=str(tmp_path),
                timeout_seconds=5,
                env={
                    "CUSTOM_TEST_VAR": "should_be_preserved"
                },  # This should be preserved
            )

            assert result.return_code == 0
            # MCP variable should be removed (isolation)
            assert "MCP_STDIO_TRANSPORT: NOT_SET" in result.stdout
            # Custom variable should be preserved
            assert "CUSTOM_TEST_VAR: should_be_preserved" in result.stdout
            # Python isolation variable should be set
            assert "PYTHONUNBUFFERED: 1" in result.stdout

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


@pytest.fixture
def test_data_dir() -> Path:
    """Fixture providing test data directory."""
    return Path(__file__).parent / "testdata" / "test_command_runner_stdio"


class TestCommandResultDataclass:
    """Test CommandResult dataclass functionality."""

    def test_command_result_creation(self) -> None:
        """Test CommandResult creation and attributes."""
        result = CommandResult(
            return_code=0,
            stdout="test output",
            stderr="",
            timed_out=False,
            execution_error=None,
            command=["python", "test.py"],
            runner_type="subprocess",
            execution_time_ms=1500,
        )

        assert result.return_code == 0
        assert result.stdout == "test output"
        assert result.stderr == ""
        assert result.timed_out is False
        assert result.execution_error is None
        assert result.command == ["python", "test.py"]
        assert result.runner_type == "subprocess"
        assert result.execution_time_ms == 1500

    def test_command_result_with_defaults(self) -> None:
        """Test CommandResult with default values."""
        result = CommandResult(
            return_code=1, stdout="", stderr="error message", timed_out=True
        )

        assert result.return_code == 1
        assert result.stdout == ""
        assert result.stderr == "error message"
        assert result.timed_out is True
        assert result.execution_error is None  # Default
        assert result.command is None  # Default
        assert result.runner_type is None  # Default
        assert result.execution_time_ms is None  # Default
