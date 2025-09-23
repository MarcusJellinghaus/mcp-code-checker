# Project Decisions Log

This document records all decisions made during the project planning discussion between the developer and Claude on September 23, 2025.

## Decision Topics and Outcomes

### 1. **Step Consolidation (Complexity Reduction)**
**Decision: A - Keep current 6-step approach**
- Rationale: More granular progress tracking preferred
- Rejected alternatives: Consolidate to 3 steps, hybrid approach

### 2. **Failure Limit Configuration**
**Decision: A - Keep hardcoded limit of 10 failures**
- Rationale: Simpler implementation, covers most use cases
- Rejected alternatives: Configurable parameter, environment variable configuration

### 3. **Print Statement Handling**
**Decision: B - Auto-add `-s` flag when `show_details=True`**
- Rationale: More convenient for LLMs, less confusion
- Implementation note: Document this behavior clearly in docstrings
- Rejected alternatives: Require explicit `-s` flag, separate parameter for print control

### 4. **Collection Errors Handling**
**Decision: B - Always show collection errors regardless of limits**
- Rationale: Critical setup issues that need immediate attention
- Implementation note: Collection errors don't count toward the 10-failure limit
- Rejected alternatives: Count toward failure limit, only show with `show_details=True`

### 5. **Auto-enabling Details for Small Test Runs**
**Decision: C - Add hints when `show_details=False` but ≤3 tests**
- Rationale: Provides smart guidance while maintaining explicit control
- Implementation note: Suggest using `show_details=True` in output when appropriate
- Rejected alternatives: Always auto-show for ≤3 tests, explicit control only

### 6. **Parameter Validation and Edge Cases**
**Decision: A - Basic validation**
- Rationale: Keep it simple, let existing layers handle complex edge cases
- Implementation: Just ensure `show_details` is boolean type
- Rejected alternatives: Comprehensive validation, defensive programming approach

### 7. **Output Format and Truncation**
**Decision: A - No per-test truncation, but overall 300-line limit with "..." indicator**
- Rationale: Show full output for each failure while preventing context overflow
- Implementation: Overall output limited to 300 lines total
- Rejected alternatives: 50 lines per test, smart scaling truncation

### 8. **Documentation Clarity**
**Decision: B - Comprehensive+ approach per Step 6 specification**
- Rationale: LLMs need detailed guidance, feature warrants thorough documentation
- Implementation: Separate usage examples file, validate examples work
- Rejected alternatives: Match current docstring style, simplified approach

## Technical Implementation Updates

Based on these decisions, the following technical specifications are updated:

### Enhanced Behavior
- **`show_details=True`**: Automatically adds `-s` flag to show print statements
- **Collection errors**: Always displayed, don't count toward failure limits
- **Smart hints**: Output includes suggestions when `show_details=False` but ≤3 tests ran
- **Output limits**: Maximum 300 lines total with truncation indicator

### Parameter Specifications
```python
def run_pytest_check(
    markers: Optional[List[str]] = None,
    verbosity: int = 2,                    # pytest's native -v (unchanged)
    extra_args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    show_details: bool = False             # NEW: LLM output control + auto -s
) -> str:
```

### Decision Logic Updates
```python
# Enhanced decision logic
def should_show_details(test_results: dict, show_details: bool) -> bool:
    if not show_details: 
        return False
    
    # Collection errors always shown (handled separately)
    total_tests = test_results.get("summary", {}).get("collected", 0)
    failures = test_results.get("summary", {}).get("failed", 0) + test_results.get("summary", {}).get("error", 0)
    
    return total_tests <= 3 or failures <= 10

# Smart hints logic  
def should_suggest_show_details(test_results: dict, show_details: bool) -> bool:
    if show_details:
        return False  # Already using details
    
    total_tests = test_results.get("summary", {}).get("collected", 0)
    return total_tests <= 3  # Suggest for small test runs
```

## Documentation Requirements

Based on Decision #8, documentation must include:
- Enhanced docstring with smart behavior explanations
- Separate usage examples file (`PR_Info/steps/show_details_usage_examples.md`)
- Validation tests that docstring examples actually work
- Clear explanation of auto-`-s` behavior
- LLM-focused usage patterns and guidance

## Next Steps

All decisions are now finalized. Implementation can proceed with the 6-step approach using these specifications.
