"""Error handling and formatting for MCP Configuration Helper.

This module provides utilities for generating actionable error messages
with helpful suggestions for users.
"""

from pathlib import Path
from typing import Any, Callable

from src.config.output import OutputFormatter


class ConfigError(Exception):
    """Base exception for configuration errors."""
    
    def __init__(
        self, 
        message: str, 
        details: str | None = None,
        suggestions: list[str] | None = None
    ):
        """Initialize configuration error.
        
        Args:
            message: Main error message
            details: Optional technical details
            suggestions: Optional list of suggestions
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggestions = suggestions or []
        
    def print_error(self) -> None:
        """Print formatted error message."""
        OutputFormatter.print_error(f"Error: {self.message}")
        
        if self.details:
            print(f"\nDetails:\n{self.details}")
            
        if self.suggestions:
            print("\nSuggestions:")
            for suggestion in self.suggestions:
                print(f"  • {suggestion}")


class MissingParameterError(ConfigError):
    """Error for missing required parameters."""
    
    def __init__(self, param_name: str, server_type: str):
        """Initialize missing parameter error.
        
        Args:
            param_name: Name of missing parameter
            server_type: Type of server being configured
        """
        message = f"Required parameter --{param_name} not specified"
        
        suggestions = [
            f"Run: mcp-config setup {server_type} <name> --{param_name} <value>",
            f"Use --help to see all available parameters",
        ]
        
        # Add specific suggestions based on parameter
        if param_name == "project-dir":
            suggestions.insert(0, "Use current directory: --project-dir .")
            suggestions.insert(1, f"Specify project path: --project-dir /path/to/project")
        elif param_name == "python-executable":
            suggestions.insert(0, "Auto-detection failed, specify Python path manually")
            suggestions.insert(1, "Example: --python-executable /usr/bin/python3.11")
            
        super().__init__(message, suggestions=suggestions)


class InvalidServerError(ConfigError):
    """Error for invalid server name or type."""
    
    def __init__(
        self, 
        server_name: str, 
        available_servers: list[str] | None = None,
        is_external: bool = False
    ):
        """Initialize invalid server error.
        
        Args:
            server_name: Name of invalid server
            available_servers: List of available servers
            is_external: Whether server is external (not managed)
        """
        if is_external:
            message = f"Server '{server_name}' exists but is not managed by mcp-config"
            suggestions = [
                "Only servers created by mcp-config can be removed",
                "List managed servers: mcp-config list --managed-only",
            ]
        else:
            message = f"Server '{server_name}' not found"
            suggestions = []
            
            if available_servers:
                suggestions.append(f"Available servers: {', '.join(available_servers)}")
                
            suggestions.extend([
                "List all servers: mcp-config list",
                "Check server name spelling",
                "Use exact server name from list output",
            ])
            
        super().__init__(message, suggestions=suggestions)


class PermissionError(ConfigError):
    """Error for file/directory permission issues."""
    
    def __init__(self, path: Path, operation: str = "access"):
        """Initialize permission error.
        
        Args:
            path: Path with permission issue
            operation: Operation that failed (read/write/execute)
        """
        message = f"Cannot {operation} path: {path}"
        
        details = f"Permission denied: {path}"
        
        suggestions = []
        
        if path.is_file():
            suggestions.append(f"Check file permissions: ls -la {path}")
            if operation == "write":
                suggestions.append(f"Fix permissions: chmod 644 {path}")
            elif operation == "execute":
                suggestions.append(f"Fix permissions: chmod 755 {path}")
        elif path.is_dir():
            suggestions.append(f"Check directory permissions: ls -la {path}")
            if operation == "write":
                suggestions.append(f"Fix permissions: chmod 755 {path}")
                
        suggestions.append("Run with proper user permissions")
        
        super().__init__(message, details=details, suggestions=suggestions)


class PathNotFoundError(ConfigError):
    """Error for missing paths."""
    
    def __init__(self, path: Path, path_type: str = "path"):
        """Initialize path not found error.
        
        Args:
            path: Missing path
            path_type: Type of path (directory/file/executable)
        """
        message = f"{path_type.capitalize()} does not exist: {path}"
        
        suggestions = []
        
        if path_type == "directory":
            suggestions.append(f"Create directory: mkdir -p {path}")
        elif path_type == "project directory":
            suggestions.append(f"Create project directory: mkdir -p {path}")
            suggestions.append("Ensure you're in the correct location")
            suggestions.append("Use --project-dir to specify the correct path")
        elif path_type == "python executable":
            suggestions.append("Install Python or update --python-executable parameter")
            suggestions.append("Check Python installation: which python3")
            suggestions.append("Use virtual environment: --venv-path /path/to/venv")
        elif path_type == "virtual environment":
            suggestions.append(f"Create virtual environment: python -m venv {path}")
            suggestions.append("Activate existing venv and retry")
            
        super().__init__(message, suggestions=suggestions)


class ConfigurationError(ConfigError):
    """Error for configuration file issues."""
    
    def __init__(
        self, 
        config_path: Path,
        error_type: str = "invalid",
        details: str | None = None
    ):
        """Initialize configuration error.
        
        Args:
            config_path: Path to configuration file
            error_type: Type of error (invalid/corrupt/missing)
            details: Additional error details
        """
        if error_type == "missing":
            message = f"Configuration file not found: {config_path}"
            suggestions = [
                "Ensure Claude Desktop is installed",
                f"Check if file exists: ls -la {config_path}",
                "Create initial configuration with setup command",
            ]
        elif error_type == "corrupt":
            message = f"Configuration file is corrupted: {config_path}"
            suggestions = [
                f"Backup current file: cp {config_path} {config_path}.backup",
                "Check JSON syntax with a validator",
                "Restore from backup if available",
            ]
        else:
            message = f"Invalid configuration: {config_path}"
            suggestions = [
                "Validate JSON syntax",
                "Check for missing required fields",
                "Review recent changes",
            ]
            
        super().__init__(message, details=details, suggestions=suggestions)


def format_error_with_suggestions(
    error_message: str,
    suggestions: list[str] | None = None,
    details: str | None = None
) -> None:
    """Format and print an error with suggestions.
    
    Args:
        error_message: Main error message
        suggestions: Optional list of suggestions
        details: Optional technical details
    """
    OutputFormatter.print_error(f"Error: {error_message}")
    
    if details:
        print(f"\nDetails:\n{details}")
        
    if suggestions:
        print("\nSuggestions:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")


def handle_common_errors(func: Callable[..., int]) -> Callable[..., int]:
    """Decorator to handle common errors with better messages.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)
        except PermissionError as e:
            path = Path(str(e)) if str(e) else Path(".")
            error = PermissionError(path, "access")
            error.print_error()
            return 1
        except FileNotFoundError as e:
            path = Path(str(e)) if str(e) else Path(".")
            file_error = PathNotFoundError(path, "file")
            file_error.print_error()
            return 1
        except ConfigError as e:
            e.print_error()
            return 1
        except Exception as e:
            format_error_with_suggestions(
                str(e),
                suggestions=[
                    "Check the error message above",
                    "Run with --verbose for more details",
                    "Report persistent issues on GitHub",
                ]
            )
            return 1
            
    return wrapper
