# FIX: Hanging Pytest Processes Issue

## Problem Description

When running `pytest tests`, subprocess pytest instances were not being properly terminated, leading to zombie/hanging processes that persisted even after the main test run completed. This was causing:

1. Multiple pytest processes accumulating over time
2. System resource exhaustion
3. Potential test interference
4. Need for manual process cleanup

## Root Cause Analysis

The issue was in the `subprocess_runner.py` module. When `subprocess.run()` encounters a timeout:

1. **On Windows**: The default `subprocess.run()` only kills the direct child process, NOT the entire process tree
2. **Pytest spawns child processes**: When pytest runs, it can spawn additional Python processes for test isolation
3. **Orphaned processes**: These grandchild processes become orphaned when only the parent pytest is killed
4. **No process group on Windows**: Windows doesn't have Unix-style process groups, making cleanup harder

### The Problematic Code

```python
# OLD CODE - Insufficient cleanup
process = subprocess.run(
    command,
    timeout=options.timeout_seconds,
    # ... other args
)
# When timeout occurs, only the direct child is killed!
```

## The Fix

### 1. Process Tree Termination

Replaced `subprocess.run()` with `subprocess.Popen()` for better control:

```python
# NEW CODE - Proper process tree cleanup
popen_proc = subprocess.Popen(command, ...)
try:
    stdout, stderr = popen_proc.communicate(timeout=timeout)
except subprocess.TimeoutExpired:
    if os.name == 'nt':
        # Windows: Use taskkill to kill entire process tree
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(popen_proc.pid)])
    else:
        # Unix: Kill the process group
        os.killpg(os.getpgid(popen_proc.pid), signal.SIGKILL)
```

### 2. Key Improvements

- **Windows**: Uses `taskkill /T` flag to kill the entire process tree
- **Unix/Linux**: Uses process groups with `os.killpg()`
- **Fallback mechanism**: If primary method fails, uses `.terminate()` then `.kill()`
- **Cleanup wait**: Waits up to 2 seconds for processes to clean up properly

### 3. Additional Safeguards

- Added subprocess depth tracking (`PYTEST_SUBPROCESS_DEPTH`)
- Created cleanup utility script (`tools/cleanup_pytest.py`)
- Added test markers to separate integration tests
- Improved logging for process lifecycle

## How to Use

### Normal Testing
```bash
# Run only unit tests (no subprocess spawning)
pytest -m "not integration"

# Run all tests (with proper cleanup)
pytest
```

### If Processes Get Stuck
```bash
# Manual cleanup
python tools/cleanup_pytest.py

# Auto-cleanup without confirmation
python tools/cleanup_pytest.py --auto

# Monitor mode
python tools/cleanup_pytest.py --loop
```

### Debugging Process Issues
```bash
# Check for hanging processes
python test_process_leak.py

# Run tests with verbose subprocess tracking
PYTEST_SUBPROCESS_DEPTH=0 pytest -v
```

## Why This Matters

1. **Resource Management**: Prevents process accumulation and memory leaks
2. **Test Reliability**: Ensures clean test environment between runs
3. **CI/CD Compatibility**: Prevents build agents from hanging
4. **Developer Experience**: No need for manual process cleanup

## Platform-Specific Notes

### Windows
- Process handling is more complex due to lack of process groups
- `taskkill /T` is used to kill process trees
- May need administrator privileges for some cleanup operations

### Linux/macOS
- Uses process groups for cleaner subprocess management
- More reliable process termination with SIGTERM/SIGKILL

## Verification

After applying the fix, running the test suite should:
1. Complete without leaving hanging processes
2. Show "Killing timed out process" warnings in logs when timeouts occur
3. Clean up all subprocesses within 2-3 seconds of test completion

## Additional Recommendations

1. **Use mocks when possible**: Reduce integration tests that spawn real subprocesses
2. **Set appropriate timeouts**: 300 seconds might be too long for most tests
3. **Monitor CI/CD**: Ensure cleanup works in your CI environment
4. **Regular cleanup**: Run cleanup script periodically during development
