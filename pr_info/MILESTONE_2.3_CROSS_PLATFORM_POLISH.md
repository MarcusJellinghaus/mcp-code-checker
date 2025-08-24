# Milestone 2.3: Cross-Platform Polish

## Overview
Ensure robust cross-platform functionality with proper Windows/Mac/Linux path handling, platform-specific configuration paths, and comprehensive error handling. This milestone focuses on production readiness and reliability across all supported platforms.

## Prerequisites
- Milestone 2.2 completed (advanced CLI features)
- Validate command implemented
- Dry-run support working
- Enhanced output formatting in place

## Goals
1. Implement robust cross-platform path handling
2. Add platform-specific configuration path detection
3. Enhance error handling for platform-specific issues
4. Add comprehensive logging and debugging capabilities
5. Ensure consistent behavior across Windows, macOS, and Linux

## Detailed Requirements

### 1. Cross-Platform Path Handling

Implement robust path handling that works consistently across all platforms:

#### Path Normalization:
```python
def normalize_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    Normalize paths for cross-platform compatibility.
    
    Features:
    - Convert backslashes to forward slashes internally
    - Handle Windows drive letters correctly
    - Resolve relative paths against base_dir
    - Expand user home directory (~)
    - Resolve symbolic links and shortcuts
    - Handle UNC paths on Windows
    - Validate path length limits per platform
    """
```

#### Platform-Specific Considerations:
1. **Windows:**
   - Handle drive letters (C:, D:)
   - Support UNC paths (\\server\share)
   - Handle path length limitations (260 chars classic, 32K extended)
   - Deal with reserved names (CON, PRN, AUX, etc.)
   - Handle case-insensitive filesystem

2. **macOS:**
   - Handle case-sensitive/insensitive filesystems
   - Deal with resource forks and extended attributes
   - Support bundle directories (.app, .framework)
   - Handle Unicode normalization (NFD vs NFC)

3. **Linux:**
   - Handle case-sensitive filesystem
   - Support various mount points and filesystem types
   - Deal with symlinks and hardlinks
   - Handle special characters in filenames

#### Virtual Environment Detection:
```python
def detect_venv_cross_platform(project_dir: Path) -> Optional[VenvInfo]:
    """
    Detect virtual environments across platforms.
    
    Patterns to check:
    - .venv/ (common)
    - venv/ (common)
    - .virtualenv/ (older pattern)
    - env/ (simple pattern)
    - Scripts/python.exe (Windows)
    - bin/python (Unix-like)
    - pyvenv.cfg file presence
    """
```

### 2. Platform-Specific Configuration Paths

Implement proper configuration directory detection for each platform:

#### Configuration Path Strategy:
```python
def get_client_config_path(client_name: str) -> Path:
    """
    Get platform-specific configuration path for MCP clients.
    
    Claude Desktop paths:
    - Windows: %APPDATA%/Claude/claude_desktop_config.json
    - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json  
    - Linux: ~/.config/claude/claude_desktop_config.json
    
    VS Code (future):
    - Windows: %APPDATA%/Code/User/settings.json
    - macOS: ~/Library/Application Support/Code/User/settings.json
    - Linux: ~/.config/Code/User/settings.json
    """
```

#### Environment Variable Handling:
- Respect XDG Base Directory Specification on Linux
- Handle Windows environment variables correctly
- Support macOS Application Support directory
- Provide fallbacks for edge cases

#### Directory Creation:
```python
def ensure_config_directory(config_path: Path) -> None:
    """
    Safely create configuration directories with proper permissions.
    
    Features:
    - Create parent directories as needed
    - Set appropriate permissions (700 for config dirs)
    - Handle permission errors gracefully  
    - Provide clear error messages for failures
    """
```

### 3. Python Executable Detection

Enhance Python executable detection for cross-platform reliability:

#### Detection Strategy:
```python
def detect_python_executable(project_dir: Path) -> PythonInfo:
    """
    Comprehensive Python executable detection.
    
    Priority order:
    1. Virtual environment in project (highest priority)
    2. Python specified in pyproject.toml requires-python
    3. Current Python executable (sys.executable)
    4. System Python on PATH
    5. Platform-specific Python locations
    
    Validation:
    - Executable exists and is runnable
    - Version compatibility checking
    - Architecture compatibility (32-bit vs 64-bit)
    """
```

#### Platform-Specific Python Locations:
1. **Windows:**
   - Python Launcher (py.exe) integration
   - Microsoft Store Python locations
   - Anaconda/Miniconda locations
   - PyInstaller frozen executables

2. **macOS:**
   - Homebrew Python (/opt/homebrew/bin, /usr/local/bin)
   - MacPorts Python (/opt/local/bin)
   - System Python (/usr/bin/python3)
   - Xcode Python locations

3. **Linux:**
   - Distribution Python (/usr/bin/python3)
   - Alternative installations (/usr/local/bin)
   - Snap packages (/snap/bin)
   - AppImage executables

### 4. Enhanced Error Handling

Implement platform-specific error handling and diagnostics:

#### Error Categories:
```python
class PlatformError(Exception):
    """Base class for platform-specific errors."""
    pass

class WindowsError(PlatformError):
    """Windows-specific errors (path length, permissions, etc.)"""
    pass

class MacOSError(PlatformError):
    """macOS-specific errors (bundle access, gatekeeper, etc.)"""
    pass

class LinuxError(PlatformError):
    """Linux-specific errors (permissions, mount points, etc.)"""
    pass
```

#### Error Diagnostics:
```python
def diagnose_platform_issue(error: Exception, context: dict) -> str:
    """
    Provide platform-specific diagnostics and solutions.
    
    Windows diagnostics:
    - Path length issues → suggest UNC or shorter paths
    - Permission issues → suggest running as administrator
    - Antivirus issues → suggest exclusion rules
    
    macOS diagnostics:
    - Gatekeeper issues → suggest security settings
    - SIP issues → suggest proper installation methods
    - Bundle access → suggest proper app permissions
    
    Linux diagnostics:
    - Permission issues → suggest proper ownership/chmod
    - Mount issues → suggest checking /etc/fstab
    - SELinux issues → suggest context adjustments
    """
```

### 5. Logging and Debugging

Add comprehensive logging for troubleshooting platform-specific issues:

#### Logging Framework:
```python
def setup_platform_logging(verbose: bool = False) -> logging.Logger:
    """
    Setup platform-aware logging.
    
    Features:
    - Platform detection and logging
    - Environment variable logging
    - Path resolution logging
    - Permission checking logging
    - Performance timing for operations
    """
```

#### Debug Information Collection:
```python
def collect_debug_info() -> dict:
    """
    Collect comprehensive platform debug information.
    
    Information collected:
    - Platform details (OS, version, architecture)
    - Python details (version, executable, paths)
    - Environment variables (relevant ones)
    - File system information
    - Permissions and access rights
    - Available disk space
    """
```

### 6. Performance Optimization

Optimize operations for each platform's characteristics:

#### Caching Strategy:
- Cache expensive operations (Python detection, path resolution)
- Platform-specific cache locations
- Cache invalidation on relevant changes

#### I/O Optimization:
- Batch file operations where possible
- Use platform-native APIs for better performance
- Optimize for platform-specific filesystem characteristics

## Implementation Tasks

### Task 1: Cross-Platform Path System (8 hours)
1. Implement robust path normalization utilities
2. Add platform-specific path handling logic
3. Create comprehensive path validation
4. Write extensive path handling tests

**Expected Files:**
- `src/config/paths.py` (new)
- `src/config/utils.py` (enhanced)
- `tests/test_config/test_paths.py` (new)
- `tests/test_config/test_cross_platform.py` (new)

### Task 2: Configuration Path Detection (4 hours)  
1. Implement platform-specific config path detection
2. Add environment variable handling
3. Create directory creation utilities
4. Write configuration path tests

**Expected Files:**
- `src/config/clients.py` (enhanced)
- `tests/test_config/test_clients_platform.py` (new)

### Task 3: Python Detection Enhancement (6 hours)
1. Enhance Python executable detection
2. Add platform-specific Python location support
3. Implement version and compatibility checking
4. Write comprehensive Python detection tests

**Expected Files:**
- `src/config/python_detection.py` (new)
- `src/config/utils.py` (enhanced)
- `tests/test_config/test_python_detection.py` (new)

### Task 4: Error Handling and Diagnostics (6 hours)
1. Create platform-specific error classes
2. Implement diagnostic and suggestion system
3. Add comprehensive error recovery
4. Write error handling tests

**Expected Files:**
- `src/config/errors.py` (enhanced)
- `src/config/diagnostics.py` (new)
- `tests/test_config/test_diagnostics.py` (new)

## Test Requirements

### Unit Tests
1. **Path Handling Tests:**
   - Test all path normalization scenarios
   - Validate platform-specific path handling
   - Test edge cases (long paths, special characters)

2. **Configuration Path Tests:**
   - Test config path detection on all platforms
   - Validate environment variable handling
   - Test directory creation with various permissions

3. **Python Detection Tests:**
   - Test detection in various scenarios
   - Validate version compatibility checking
   - Test platform-specific Python locations

4. **Error Handling Tests:**
   - Test all platform-specific error scenarios
   - Validate diagnostic message generation
   - Test error recovery mechanisms

### Integration Tests
1. **Cross-Platform Scenarios:**
   - Test full workflow on simulated different platforms
   - Validate configuration generation across platforms
   - Test error scenarios with platform-specific issues

### Manual Testing Requirements
Each platform should be manually tested with:
- Different Python installations
- Various project structures
- Permission-restricted scenarios
- Edge cases (long paths, special characters)

## Platform-Specific Test Scenarios

### Windows Testing:
- Long path names (>260 characters)
- UNC paths (\\server\share)
- Reserved file names (CON, PRN, etc.)
- Different drive letters
- Windows Store Python
- Anaconda installations

### macOS Testing:
- Case-insensitive filesystem
- Bundle directories (.app)
- Homebrew Python installations
- Gatekeeper restrictions
- Unicode filename normalization
- System Integrity Protection (SIP)

### Linux Testing:
- Various distributions (Ubuntu, CentOS, etc.)
- Different filesystem types (ext4, btrfs, etc.)
- Symlinked directories
- Permission restrictions
- Snap/Flatpak applications
- Different desktop environments

## Acceptance Criteria

### Must Have:
1. All functionality works consistently across Windows, macOS, and Linux
2. Path handling is robust and secure on all platforms
3. Configuration paths are detected correctly on all platforms
4. Python detection works with common installation patterns
5. Error messages are platform-appropriate and actionable

### Should Have:
1. Performance is optimized for each platform's characteristics  
2. Caching reduces repeated expensive operations
3. Debug information collection helps with troubleshooting
4. Graceful degradation when platform features are unavailable

### Test Coverage:
- Minimum 85% code coverage for cross-platform code
- All major platform scenarios tested
- Error conditions properly handled
- Platform-specific edge cases covered

## Example Cross-Platform Behavior

### Windows:
```bash
# Auto-detects Windows paths
mcp-config setup mcp-code-checker "win-checker" --project-dir C:\Users\user\project

# Output shows Windows-style paths
✓ Project directory exists: C:\Users\user\project  
✓ Python executable found: C:\Users\user\project\.venv\Scripts\python.exe
✓ Configuration: C:\Users\user\AppData\Roaming\Claude\claude_desktop_config.json
```

### macOS:
```bash
# Auto-detects macOS paths  
mcp-config setup mcp-code-checker "mac-checker" --project-dir ~/project

# Output shows Unix-style paths
✓ Project directory exists: /Users/user/project
✓ Python executable found: /Users/user/project/.venv/bin/python  
✓ Configuration: /Users/user/Library/Application Support/Claude/claude_desktop_config.json
```

### Linux:
```bash
# Auto-detects Linux paths
mcp-config setup mcp-code-checker "linux-checker" --project-dir ./project

# Output shows Unix-style paths
✓ Project directory exists: /home/user/project
✓ Python executable found: /home/user/project/.venv/bin/python
✓ Configuration: /home/user/.config/claude/claude_desktop_config.json
```

## Deliverables

1. **Cross-Platform Path System:** Robust path handling for all platforms
2. **Platform-Specific Config Detection:** Proper configuration file locations
3. **Enhanced Python Detection:** Comprehensive Python executable discovery
4. **Platform Error Handling:** Specific diagnostics and suggestions for each platform
5. **Comprehensive Testing:** Full test coverage for cross-platform scenarios
6. **Debug and Logging:** Detailed logging for troubleshooting platform issues

This milestone ensures the configuration tool is production-ready and provides consistent, reliable behavior across all supported platforms while handling platform-specific edge cases gracefully.
