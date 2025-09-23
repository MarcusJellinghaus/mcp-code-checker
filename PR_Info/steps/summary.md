# Summary: Add `show_details` Parameter to Pytest Interface

## Overview
Enhance the MCP pytest interface by adding a `show_details` parameter to `run_pytest_check()` that provides LLMs with smart control over test output verbosity without conflicting with pytest's native `-v`/`--verbose` flags.

## Problem Statement
Currently, the pytest interface only shows detailed output (including print statements) for failed tests. LLMs need more control over when to see detailed information, especially for:
- Focused testing sessions (≤3 tests)
- Debugging specific test failures 
- Analyzing print output from tests

The existing `verbosity` parameter controls pytest's internal verbosity but doesn't control what output is shown to LLMs.

## Solution
Add a `show_details: bool = False` parameter that intelligently controls LLM-visible output:

**When `show_details=True`:**
- Show detailed output for up to 10 failing tests
- Show details even for passing tests if ≤3 total tests were run
- Include print statements, tracebacks, and diagnostic information

**When `show_details=False` (default):**
- Maintain current behavior (backward compatible)
- Only show summary information for large test runs
- Provide helpful hints about using `show_details=True`

## Key Benefits
1. **No Parameter Confusion**: Uses `show_details` instead of competing with pytest's `-v`
2. **Smart Defaults**: Auto-shows details when it makes sense (focused testing)
3. **Token Management**: Prevents LLM context overflow with intelligent limits
4. **Backward Compatible**: Default behavior unchanged
5. **Test Selection**: LLMs can already select specific tests via `extra_args`

## Architectural & Design Changes

### System Architecture Overview
The enhancement follows a **layered architecture** approach with minimal changes to existing components:

```
MCP Client (LLM)
    ↓ show_details parameter
Server Layer (server.py)
    ↓ enhanced parameter passing
Reporting Layer (reporting.py)  
    ↓ controlled output formatting
Execution Layer (runners.py)
    ↓ unchanged - existing pytest execution
Subprocess Layer (subprocess_runner.py)
    ↓ unchanged - existing output capture
```

### Key Design Patterns

#### 1. **Parameter Enhancement Pattern**
- **Backward Compatibility**: New optional parameter with sensible default
- **Progressive Enhancement**: Existing behavior preserved, new functionality additive
- **Clear Separation**: `verbosity` (pytest internal) vs `show_details` (LLM output control)

#### 2. **Smart Decision Logic Pattern**  
```python
# Centralized decision logic
def should_show_details(test_results: dict, show_details: bool) -> bool:
    if not show_details: return False
    return (test_count <= 3) or (failure_count <= 10)
```

#### 3. **Controlled Output Pattern**
- **Input Validation**: Parameter type checking and bounds validation
- **Output Limiting**: Maximum failures (10), maximum lines per test (50)
- **Content Filtering**: Include/exclude print statements based on context

### Component Changes

#### **Server Layer** (`src/mcp_code_checker/server.py`)
```python
# BEFORE:
def run_pytest_check(markers, verbosity, extra_args, env_vars) -> str:

# AFTER:
def run_pytest_check(markers, verbosity, extra_args, env_vars, show_details=False) -> str:
```
**Changes**: 
- Add `show_details: bool = False` parameter
- Replace `_format_pytest_result()` calls with `_format_pytest_result_with_details()`
- Add smart decision logic integration

#### **Reporting Layer** (`src/mcp_code_checker/code_checker_pytest/reporting.py`)
```python
# BEFORE:
def create_prompt_for_failed_tests(test_session_result, max_number_of_tests_reported=1):

# AFTER:  
def create_prompt_for_failed_tests(
    test_session_result, 
    max_number_of_tests_reported=1,
    include_print_output=True,    # NEW
    max_failures=10               # NEW
):
```
**Changes**:
- Add output control parameters
- Implement content filtering logic
- Add `should_show_details()` helper function

#### **Execution & Subprocess Layers** (No Changes)
- `runners.py`: Unchanged - existing pytest execution logic preserved
- `subprocess_runner.py`: Unchanged - existing output capture preserved
- **Rationale**: Separation of concerns - these layers handle execution, not presentation

### Data Flow Architecture

#### **Before** (Current State):
```
LLM Request → Server → Runners → Subprocess → Raw Results → Fixed Formatting → LLM
```

#### **After** (Enhanced State):
```
LLM Request (+ show_details) → Server (decision logic) → Runners (unchanged) → 
Subprocess (unchanged) → Raw Results → Smart Formatting (controlled) → LLM
```

### Design Principles Applied

#### **1. Single Responsibility Principle**
- **Server Layer**: Parameter handling and orchestration
- **Reporting Layer**: Output formatting and content control  
- **Execution Layer**: Test execution only (unchanged)

#### **2. Open/Closed Principle** 
- **Open for Extension**: New parameters and formatting options
- **Closed for Modification**: Core execution logic unchanged

#### **3. Dependency Inversion**
- Server depends on reporting abstractions, not concrete implementations
- Reporting functions accept configuration parameters rather than hard-coded behavior

### Interface Design

#### **Parameter Hierarchy**
```python
run_pytest_check(
    # Test Selection (unchanged)
    markers: Optional[List[str]] = None,
    extra_args: Optional[List[str]] = None,
    
    # Execution Control (unchanged)  
    verbosity: int = 2,           # pytest's -v/-vv/-vvv
    env_vars: Optional[Dict] = None,
    
    # Output Control (NEW)
    show_details: bool = False    # LLM output verbosity
)
```

#### **Clear Separation of Concerns**
- `verbosity`: Controls pytest's internal logging and test discovery detail
- `show_details`: Controls what output is shown to LLMs
- `extra_args`: Allows direct pytest parameter control (e.g., `-s` for print statements)

### Backward Compatibility Strategy

#### **Default Behavior Preservation**
- `show_details=False` produces identical output to current implementation
- All existing function signatures remain compatible
- No changes to existing test execution or output capture

#### **Progressive Enhancement**
- New functionality only activated when explicitly requested
- Existing LLM interactions work unchanged  
- New parameter provides additional capability without breaking existing usage

### Error Handling & Edge Cases

#### **Graceful Degradation**
- Invalid parameter values fall back to safe defaults
- Output length limits prevent token overflow
- Failed detail formatting falls back to summary output

#### **Resource Management**
- Output size limits prevent memory issues
- Processing time limits prevent performance degradation
- Clean parameter validation prevents runtime errors

## Technical Approach
- **Test-Driven Development**: Each step implements tests first, then functionality
- **Minimal Changes**: Enhance existing functions rather than rewriting
- **KISS Principle**: Simple boolean parameter with smart logic
- **Integration Points**: Extends `create_prompt_for_failed_tests()` and `_format_pytest_result()`

## Implementation Steps
1. **Tests for reporting enhancements** (output control logic)
2. **Enhanced reporting functions** (add `include_print_output` parameter)  
3. **Tests for server interface** (new parameter integration)
4. **Server interface updates** (add `show_details` parameter)
5. **Integration tests** (end-to-end validation)

## Success Criteria
- LLMs can control pytest output detail level
- Backward compatibility maintained
- Smart automatic behavior for focused testing
- Clear parameter names without confusion
- Comprehensive test coverage
