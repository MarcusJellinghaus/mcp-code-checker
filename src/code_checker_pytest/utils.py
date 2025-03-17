"""
Utility functions for code checker pytest operations.
"""


def read_file(file_path: str) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        The contents of the file as a string

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If access to the file is denied
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()
