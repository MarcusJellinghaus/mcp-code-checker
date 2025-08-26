# Step 7: Final Cleanup and Dead Code Removal

## Objective
Remove any code that became unused after our simplifications.

## Tasks

1. **Remove unused imports**
   - Check all files for imports no longer needed
   - Remove imports only used by deleted functions

2. **Remove unused functions**
   - Check if any functions in `discovery.py` are only called by init
   - Remove helper functions that are no longer needed
   - Check `cli_utils.py` for unused parser helpers

3. **Simplify initialization**
   - Since init command is gone, check if we can simplify `initialize_all_servers()`
   - Remove verbose parameter if only used by init
   - Simplify the __init__.py file

4. **Remove unused parameters**
   - Check all functions for parameters that are no longer used
   - Remove default parameters that are never changed

5. **Consolidate similar functions**
   - Look for functions that do almost the same thing
   - Merge them into one simpler function

## Files to Check
- `src/config/__init__.py` - simplify initialization
- `src/config/discovery.py` - remove unused discovery functions
- `src/config/cli_utils.py` - remove unused parser utilities  
- `src/config/main.py` - clean up imports and dispatcher
- `src/config/output.py` - remove unused formatters
- `src/config/validation.py` - remove complex validators

## Tools to Help
After changes, run:
- `pylint` to find unused imports
- `grep -r "function_name"` to check if functions are used
- Tests to ensure nothing broke

## Success Metrics
- Total lines of code reduced by at least 20%
- Number of functions reduced
- All tests still pass
