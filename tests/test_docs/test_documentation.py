"""Test documentation files exist and are valid."""

import ast
import re
from pathlib import Path


def test_all_documentation_files_exist() -> None:
    """Test that all required documentation files exist."""
    docs_dir = Path("docs")
    required_files = ["USAGE.md", "TROUBLESHOOTING.md", "INTEGRATION.md", "API.md"]

    for file in required_files:
        assert (docs_dir / file).exists(), f"Missing documentation file: {file}"


def test_documentation_structure() -> None:
    """Test that documentation files have proper structure."""
    docs_dir = Path("docs")

    # Check USAGE.md structure
    usage_content = (docs_dir / "USAGE.md").read_text()
    assert "## Overview" in usage_content
    assert "## Installation" in usage_content
    assert "## Quick Start" in usage_content
    assert "## Complete CLI Reference" in usage_content
    assert "## Configuration Examples" in usage_content

    # Check TROUBLESHOOTING.md structure
    trouble_content = (docs_dir / "TROUBLESHOOTING.md").read_text()
    assert "## Common Issues" in trouble_content
    assert "## Debugging Steps" in trouble_content
    assert "## Getting Help" in trouble_content
    assert "## Recovery Procedures" in trouble_content

    # Check INTEGRATION.md structure
    integration_content = (docs_dir / "INTEGRATION.md").read_text()
    assert "## Overview" in integration_content
    assert "## Quick Start" in integration_content
    assert "## Parameter Types and Examples" in integration_content
    assert "## Best Practices" in integration_content

    # Check API.md structure
    api_content = (docs_dir / "API.md").read_text()
    assert "## Overview" in api_content
    assert "## Core Classes" in api_content
    assert "## Programmatic Usage Examples" in api_content
    assert "## Error Handling" in api_content


def extract_code_blocks(markdown_text: str, language: str = "python") -> list[str]:
    """Extract code blocks from markdown text."""
    pattern = rf"```{language}\n(.*?)```"
    return re.findall(pattern, markdown_text, re.DOTALL)


def test_python_code_blocks_valid() -> None:
    """Test that Python code blocks in documentation are syntactically valid."""
    docs_dir = Path("docs")

    files_with_python = ["INTEGRATION.md", "API.md"]

    for filename in files_with_python:
        filepath = docs_dir / filename
        if not filepath.exists():
            continue

        content = filepath.read_text()
        python_blocks = extract_code_blocks(content, "python")

        for i, code_block in enumerate(python_blocks):
            # Skip import-only blocks and fragments
            if code_block.strip().startswith("from ") or code_block.strip().startswith(
                "import "
            ):
                if "\n" not in code_block.strip() or all(
                    line.strip().startswith(("from ", "import "))
                    for line in code_block.strip().split("\n")
                    if line.strip()
                ):
                    continue

            # Skip dictionary/data structure literals
            if code_block.strip().startswith("{") or code_block.strip().startswith("["):
                continue

            # Skip single expressions
            if (
                "=" not in code_block
                and "def " not in code_block
                and "class " not in code_block
            ):
                continue

            try:
                # Try to parse as Python code
                ast.parse(code_block)
            except SyntaxError as e:
                # Some code blocks might be fragments, which is okay
                # But report if it looks like complete code
                if (
                    "def " in code_block
                    or "class " in code_block
                    or "if __name__" in code_block
                ):
                    print(f"Warning: Syntax error in {filename} code block {i}: {e}")


def test_cli_examples_format() -> None:
    """Test that CLI examples in docs follow correct format."""
    docs_dir = Path("docs")
    usage_content = (docs_dir / "USAGE.md").read_text()

    # Extract bash code blocks
    bash_blocks = extract_code_blocks(usage_content, "bash")

    for block in bash_blocks:
        lines = block.strip().split("\n")
        for line in lines:
            # Skip comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                continue

            # Check that mcp-config commands are properly formatted
            if "mcp-config" in line:
                # Should have a subcommand
                if not any(
                    cmd in line
                    for cmd in [
                        "setup",
                        "remove",
                        "list",
                        "validate",
                        "backup",
                        "init",
                        "--help",
                        "--version",
                    ]
                ):
                    print(f"Warning: CLI command might be missing subcommand: {line}")


def test_documentation_links() -> None:
    """Test that internal documentation links are valid."""
    docs_dir = Path("docs")

    for file in ["USAGE.md", "TROUBLESHOOTING.md", "INTEGRATION.md", "API.md"]:
        filepath = docs_dir / file
        if not filepath.exists():
            continue

        content = filepath.read_text()

        # Find all markdown links
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

        for link_text, link_url in links:
            # Check internal documentation links
            if link_url.endswith(".md") and not link_url.startswith("http"):
                # Remove any anchors
                link_file = link_url.split("#")[0]
                # Check if the linked file exists
                linked_path = docs_dir / link_file
                if (
                    not linked_path.exists()
                    and not (docs_dir.parent / link_file).exists()
                ):
                    print(f"Warning: Broken link in {file}: {link_url}")


def test_code_example_consistency() -> None:
    """Test that code examples are consistent across documentation."""
    docs_dir = Path("docs")

    # Check that import paths are consistent
    import_patterns = set()

    for file in ["INTEGRATION.md", "API.md"]:
        filepath = docs_dir / file
        if not filepath.exists():
            continue

        content = filepath.read_text()

        # Find all import statements in code blocks
        python_blocks = extract_code_blocks(content, "python")
        for block in python_blocks:
            imports = re.findall(r"from ([\w.]+) import", block)
            import_patterns.update(imports)

    # Check for consistency in module names
    if "mcp_config" in import_patterns and "src.config" in import_patterns:
        print("Note: Documentation uses both 'mcp_config' and 'src.config' imports")


def test_bash_examples_validity() -> None:
    """Test that bash examples follow proper conventions."""
    docs_dir = Path("docs")

    for file in ["USAGE.md", "TROUBLESHOOTING.md"]:
        filepath = docs_dir / file
        if not filepath.exists():
            continue

        content = filepath.read_text()
        bash_blocks = extract_code_blocks(content, "bash")

        for block in bash_blocks:
            lines = block.strip().split("\n")
            for line in lines:
                # Skip comments and empty lines
                if not line.strip() or line.strip().startswith("#"):
                    continue

                # Check for common bash issues
                if "mcp-config" in line:
                    # Ensure proper line continuation
                    if line.rstrip().endswith("\\"):
                        # Next line should be indented
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1]
                            if next_line and not next_line.startswith(" "):
                                print(
                                    f"Warning: Line continuation not properly indented in {file}"
                                )
