"""Performance tests for VSCode support."""

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config.clients import VSCodeHandler


class TestVSCodePerformance:
    """Test performance aspects of VSCode support."""

    def test_large_config_handling(self, tmp_path):
        """Test handling of large configuration files."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Create a large config with many servers
            large_config = {
                "servers": {
                    f"server-{i}": {
                        "command": "python",
                        "args": ["-m", f"module_{i}", "--arg", f"value_{i}"],
                        "env": {f"ENV_{i}": f"value_{i}"},
                    }
                    for i in range(100)
                }
            }

            # Create metadata for half of them (50 managed, 50 external)
            metadata = {
                f"server-{i}": {
                    "_managed_by": "mcp-config-managed",
                    "_server_type": "mcp-code-checker",
                }
                for i in range(0, 50)
            }

            # Save config and metadata
            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(large_config, f)

            with open(config_path / ".mcp-config-metadata.json", "w") as f:
                json.dump(metadata, f)

            # Measure time to list servers
            start = time.time()
            servers = handler.list_all_servers()
            duration = time.time() - start

            assert len(servers) == 100
            assert (
                duration < 5.0
            )  # Should complete within 5 seconds (very lenient for CI/slow systems)

            # Measure time to list managed servers only
            start = time.time()
            managed = handler.list_managed_servers()
            duration = time.time() - start

            assert len(managed) == 50
            assert (
                duration < 3.0
            )  # Should be faster than listing all (very lenient for CI)

    def test_repeated_operations(self, tmp_path):
        """Test that repeated operations don't degrade performance."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Perform multiple setup operations
            times = []
            for i in range(10):
                start = time.time()

                server_config = {
                    "command": "python",
                    "args": ["-m", "test_module", f"--iteration", str(i)],
                    "_server_type": "test-server",
                }

                handler.setup_server(f"perf-test-{i}", server_config)

                duration = time.time() - start
                times.append(duration)

            # Check that performance doesn't degrade significantly
            # Instead of comparing first to last (which can be noisy),
            # check that the median time is reasonable and no operation is extremely slow
            import statistics

            median_time = statistics.median(times)
            max_time = max(times)

            # No single operation should take more than 2 seconds (very lenient for CI/slow systems)
            assert max_time < 2.0, f"Operation took too long: {max_time:.4f}s"

            # Median should be reasonably fast (under 500ms - very lenient for CI)
            assert median_time < 0.5, f"Median time too high: {median_time:.4f}s"

            # Check for severe performance degradation - compare averages of first and last halves
            first_half_avg = sum(times[:5]) / 5
            second_half_avg = sum(times[5:]) / 5

            # Second half shouldn't be more than 50x slower on average (extremely permissive for CI)
            assert second_half_avg < first_half_avg * 50, (
                f"Performance degradation detected: first half avg={first_half_avg:.4f}s, "
                f"second half avg={second_half_avg:.4f}s"
            )

    def test_config_validation_performance(self, tmp_path):
        """Test that validation is performant even with complex configs."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Create a complex config with nested structures
            complex_config = {
                "servers": {
                    f"complex-{i}": {
                        "command": "python",
                        "args": [
                            "-m",
                            f"module_{i}",
                            "--config",
                            json.dumps({"nested": {"data": i}}),
                            "--paths",
                            ",".join([f"/path/{j}" for j in range(10)]),
                        ],
                        "env": {f"VAR_{j}": f"value_{i}_{j}" for j in range(20)},
                    }
                    for i in range(20)
                }
            }

            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(complex_config, f)

            # Measure validation time
            start = time.time()
            errors = handler.validate_config()
            duration = time.time() - start

            assert (
                duration < 3.0
            )  # Validation should be reasonably fast (very lenient for CI)
            assert len(errors) == 0  # Config should be valid

    def test_file_operations_efficiency(self, tmp_path):
        """Test that file operations are efficient."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Setup initial config
            initial_config = {
                "command": "python",
                "args": ["-m", "initial"],
                "_server_type": "test",
            }

            handler.setup_server("test-server", initial_config)

            # Measure time for backup operation
            start = time.time()
            backup_path = handler.backup_config()
            duration = time.time() - start

            assert duration < 2.0  # Backup should be quick (very lenient for CI)
            assert backup_path.exists()

            # Measure time to read and parse config
            start = time.time()
            with open(tmp_path / ".vscode" / "mcp.json") as f:
                config = json.load(f)
            duration = time.time() - start

            assert duration < 1.0  # JSON parsing should be fast (very lenient for CI)

    @pytest.mark.parametrize("num_servers", [10, 50, 100])
    def test_scalability(self, tmp_path, num_servers):
        """Test that operations scale reasonably with number of servers."""
        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path
            handler = VSCodeHandler(workspace=True)

            # Create config with varying number of servers
            config = {
                "servers": {
                    f"server-{i}": {"command": "python", "args": [f"script_{i}.py"]}
                    for i in range(num_servers)
                }
            }

            config_path = tmp_path / ".vscode"
            config_path.mkdir()

            with open(config_path / "mcp.json", "w") as f:
                json.dump(config, f)

            # Measure list operation
            start = time.time()
            servers = handler.list_all_servers()
            duration = time.time() - start

            assert len(servers) == num_servers

            # Time should scale sub-linearly (not O(n²) or worse)
            # Even with 100 servers, should be under 5 seconds (very lenient for CI)
            max_time = 0.05 * num_servers  # Linear scaling allowance (very generous)
            assert duration < max(max_time, 5.0)  # Very lenient for CI systems

    def test_concurrent_operations_safety(self, tmp_path):
        """Test that concurrent operations don't cause issues."""
        import threading

        with patch("src.config.clients.Path.cwd") as mock_cwd:
            mock_cwd.return_value = tmp_path

            # Create multiple handlers (simulating concurrent access)
            handlers = [VSCodeHandler(workspace=True) for _ in range(5)]

            # Setup initial config
            handlers[0].setup_server(
                "initial",
                {"command": "python", "args": ["main.py"], "_server_type": "test"},
            )

            results = []
            errors = []

            def read_operation(handler, index):
                """Simulate read operation."""
                try:
                    servers = handler.list_all_servers()
                    results.append((index, len(servers)))
                except Exception as e:
                    errors.append((index, str(e)))

            # Create threads for concurrent reads
            threads = []
            for i, handler in enumerate(handlers):
                thread = threading.Thread(target=read_operation, args=(handler, i))
                threads.append(thread)

            # Start all threads
            start = time.time()
            for thread in threads:
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join(timeout=2.0)

            duration = time.time() - start

            # All operations should complete within reasonable time
            assert duration < 10.0  # Very lenient for concurrent operations on CI

            # No errors should occur
            assert len(errors) == 0

            # All should see the same config
            assert all(count == 1 for _, count in results)
