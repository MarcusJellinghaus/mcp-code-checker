"""MCP Code Checker - An MCP server for running Python code checks."""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version("mcp-code-checker")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = ["__version__"]
