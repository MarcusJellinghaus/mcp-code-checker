# Test Failure Analysis: test_dry_run.py

## Problem Summary
The test `test_setup_dry_run` in `tests/test_config/test_dry_run.py` is failing because of a parameter format mismatch in the validation logic.

## Root Cause Analysis

### The Issue
The `validate_required_parameters` function in `src/config/utils.py` has a logic error when checking for required parameters:

1. **Input Format**: The function receives `user_params` in **hyphen format** (e.g., `{"project-dir": "..."}`)
2. **Check Logic**: But it converts parameter names to **underscore format** to look them up in the dict
3. **Result**: The lookup fails because it's searching for `"project_dir"` in a dict that has `"project-dir"`

### Code Flow
```python
# In generate_client_config (src/config/integration.py):
# 1. Converts user_params from underscore to hyphen format
hyphen_params = {}
for key, value in user_params.items():
    hyphen_key = key.replace("_", "-")
    hyphen_params[hyphen_key] = value

# 2. Passes hyphen_params to validate_required_parameters
errors = validate_required_parameters(server_config, hyphen_params)

# In validate_required_parameters (src/config/utils.py):
# 3. BUT it converts param names to underscore format for lookup!
for param in server_config.parameters:
    if param.required:
        param_key = param.name.replace("-", "_")  # Convert to underscore
        if param_key not in user_params:  # But user_params has hyphen keys!
            errors.append(f"{param.name} is required")
```

## The Fix

### Option 1: Fix validate_required_parameters (Recommended)
Change `validate_required_parameters` to not convert the parameter names:

```python
def validate_required_parameters(
    server_config: ServerConfig, user_params: dict[str, Any]
) -> list[str]:
    """Validate that all required parameters are provided.
    
    Args:
        server_config: Server configuration with parameter definitions
        user_params: User-provided parameters (in hyphen format)
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []
    
    for param in server_config.parameters:
        if param.required:
            # Don't convert - expect hyphen format in user_params
            if param.name not in user_params or user_params[param.name] is None:
                errors.append(f"{param.name} is required")
    
    return errors
```

### Option 2: Pass Original Format
Alternatively, pass the original underscore format to `validate_required_parameters`, but this would require more changes.

## Impact Analysis

### Files to Change
- `src/config/utils.py`: Update `validate_required_parameters` function

### Test Coverage
After the fix, the following tests should pass:
- `test_setup_dry_run`
- `test_dry_run_validation_succeeds_when_params_valid`
- All other dry-run related tests

### Backward Compatibility
This change maintains backward compatibility as it fixes a bug in the internal validation logic without changing the public API.

## Verification Steps
1. Apply the fix to `src/config/utils.py`
2. Run the specific test: `pytest tests/test_config/test_dry_run.py::TestDryRunFunctionality::test_setup_dry_run -v`
3. Run all dry-run tests: `pytest tests/test_config/test_dry_run.py -v`
4. Run full test suite to ensure no regressions
