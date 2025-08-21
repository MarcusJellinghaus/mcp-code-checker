# Testing Guide: Preventing Pytest Subprocess Spawning Issues

## The Issue

When running `pytest tests`, you may notice multiple pytest processes spawning. This happens because:

1. **Integration tests** in `tests/test_code_checker/test_runners.py` actually call the `run_tests()` function
2. `run_tests()` spawns a **new pytest subprocess** to test code in temporary directories  
3. Each integration test creates its own subprocess, leading to multiple pytest processes

This is **not a circular reference** problem, but rather expected behavior for integration tests that test the pytest runner itself.

## Solution Implemented

We've implemented several safeguards:

### 1. Test Markers
Tests are now marked as either `unit` or `integration`:
- **Unit tests**: Use mocks, don't spawn subprocesses
- **Integration tests**: Actually run pytest in subprocesses

### 2. Recursion Protection
The `run_tests()` function now:
- Tracks subprocess depth via `PYTEST_SUBPROCESS_DEPTH` environment variable
- Logs warnings if nested pytest execution is detected
- Prevents infinite recursion

### 3. Improved Configuration
Updated `pyproject.toml` with:
- Test markers for categorization
- Strict marker enforcement
- Clear documentation

## How to Run Tests

### Run only unit tests (fast, no subprocess spawning):
```bash
pytest -m "not integration"
```

### Run only integration tests (will spawn subprocesses):
```bash
pytest -m integration
```

### Run all tests:
```bash
pytest
```

### Run tests with verbose subprocess tracking:
```bash
PYTEST_SUBPROCESS_DEPTH=0 pytest -v
```

## Best Practices

1. **Default to unit tests** for development - they're faster and don't spawn subprocesses
2. **Run integration tests** separately when needed
3. **Use mocks** whenever possible to avoid subprocess spawning
4. **Monitor the depth** environment variable if you suspect recursion issues

## Debugging

If you see too many processes:

1. Check which tests are running:
   ```bash
   pytest --collect-only -m integration
   ```

2. Run with subprocess tracking:
   ```bash
   python test_circular_check.py  # While tests are running
   ```

3. Check the logs for recursion warnings

## File Structure

```
tests/
├── test_code_checker/
│   ├── test_runners.py          # Contains integration tests (marked)
│   ├── test_parsers.py          # Unit tests (mocked)
│   ├── test_models.py           # Unit tests (mocked)
│   └── test_reporting.py        # Unit tests (mocked)
└── test_spawning_issue.py       # Diagnostic test
```

## Additional Notes

- The subprocess spawning is **intentional** for integration tests
- There's **no circular reference** - subprocesses run on isolated temp directories
- The 300-second timeout prevents any infinite loops
- Recursion depth tracking provides an additional safety net
