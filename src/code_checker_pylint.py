import json
import logging
import os
import subprocess
import sys
import time
from enum import Enum
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PylintMessageType(Enum):
    """Categories for Pylint message types."""

    CONVENTION = "convention"
    REFACTOR = "refactor"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


# Default categories for pylint checks - used when no categories are specified
DEFAULT_CATEGORIES: Set[PylintMessageType] = {
    PylintMessageType.ERROR,
    PylintMessageType.FATAL,
}


class PylintMessage(NamedTuple):
    """Represents a single Pylint message."""

    type: str
    module: str
    obj: str
    line: int
    column: int
    # endLine and endColumn missing
    path: str
    symbol: str
    message: str
    message_id: str


class PylintResult(NamedTuple):
    """Represents the overall result of a Pylint run."""

    return_code: int
    messages: List[PylintMessage]
    error: Optional[str] = None  # Capture any execution errors
    raw_output: Optional[str] = None  # Capture raw output from pylint

    def get_message_ids(self) -> Set[str]:
        """Returns a set of all unique message IDs."""
        return {message.message_id for message in self.messages}

    def get_messages_filtered_by_message_id(
        self, message_id: str
    ) -> List[PylintMessage]:
        """Returns a list of messages filtered by the given message ID."""
        return [
            message for message in self.messages if message.message_id == message_id
        ]


# For backward compatibility
PylintCategory = PylintMessageType


def normalize_path(path: str, base_dir: str) -> str:
    """
    Normalize a path relative to the base directory.

    Args:
        path: The path to normalize
        base_dir: The base directory to make the path relative to

    Returns:
        Normalized path
    """
    # Replace backslashes with platform-specific separator
    normalized_path = path.replace("\\", os.path.sep).replace("/", os.path.sep)

    # Make path relative to base_dir if it starts with base_dir
    if normalized_path.startswith(base_dir):
        prefix = base_dir
        if not prefix.endswith(os.path.sep):
            prefix += os.path.sep
        normalized_path = normalized_path.replace(prefix, "", 1)

    return normalized_path


def filter_pylint_codes_by_category(
    pylint_codes: Set[str],
    categories: Set[PylintMessageType],
) -> Set[str]:
    """
    Filters Pylint codes based on the specified categories.

    Args:
        pylint_codes: A set of Pylint codes (e.g., {"C0301", "R0201", "W0613", "E0602", "F0001"}).
        categories: A set of PylintMessageType enums to filter by (e.g., {PylintMessageType.ERROR, PylintMessageType.FATAL}).

    Returns:
        A set of Pylint codes that match the specified categories.
    """
    category_prefixes = {
        PylintMessageType.CONVENTION: "C",
        PylintMessageType.REFACTOR: "R",
        PylintMessageType.WARNING: "W",
        PylintMessageType.ERROR: "E",
        PylintMessageType.FATAL: "F",
    }
    filtered_codes: Set[str] = set()
    for code in pylint_codes:
        for category in categories:
            if code.startswith(category_prefixes[category]):
                filtered_codes.add(code)
                break
    return filtered_codes


def get_pylint_results(
    project_dir: str,
    disable_codes: Optional[List[str]] = None,
    python_executable: Optional[str] = None,
) -> PylintResult:
    """
    Runs pylint on the specified project directory and returns the results.

    Args:
        project_dir: The path to the project directory.
        disable_codes: List of pylint codes to disable during analysis. Common codes include:
            - C0114: Missing module docstring
            - C0116: Missing function docstring
            - C0301: Line too long
            - C0303: Trailing whitespace
            - C0305: Trailing newlines
            - W0311: Bad indentation
            - W0611: Unused import
            - W1514: Unspecified encoding
        python_executable: Path to Python executable to use for running pylint. Defaults to sys.executable if None.

    Returns:
        A PylintResult object containing the results of the pylint run.

    Raises:
        FileNotFoundError: If the project directory does not exist.
    """
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    try:
        # Determine the Python executable from the parameter or fall back to sys.executable
        python_exe = (
            python_executable if python_executable is not None else sys.executable
        )

        # Construct the pylint command
        pylint_command = [
            python_exe,
            "-m",
            "pylint",
            "--output-format=json",
        ]

        if disable_codes and len(disable_codes) > 0:
            pylint_command.append(f"--disable={','.join(disable_codes)}")
        pylint_command.append("src")
        if os.path.exists(os.path.join(project_dir, "tests")):
            pylint_command.append("tests")

        # Run pylint and capture its output
        logger.debug(f"Running pylint command: {' '.join(pylint_command)}")
        process = subprocess.run(
            pylint_command, cwd=project_dir, capture_output=True, text=True, check=False
        )

        raw_output = process.stdout

        # Parse pylint output from JSON, if available
        messages: List[PylintMessage] = []

        try:
            pylint_output = json.loads(process.stdout)
            for item in pylint_output:
                messages.append(
                    PylintMessage(
                        type=item.get("type", ""),
                        module=item.get("module", ""),
                        obj=item.get("obj", ""),
                        line=item.get("line", -1),
                        column=item.get("column", -1),
                        path=item.get("path", ""),
                        symbol=item.get("symbol", ""),
                        message=item.get("message", ""),
                        message_id=item.get("message-id", ""),
                    )
                )
        except json.JSONDecodeError as e:
            error_message = (
                f"Failed to parse Pylint JSON output: {e}. "
                f"First 100 chars of output: {raw_output[:100]}..."
                if len(raw_output) > 100
                else raw_output
            )
            result = PylintResult(
                return_code=process.returncode,
                messages=[],
                error=error_message,
                raw_output=raw_output,
            )
            return result

        result = PylintResult(
            return_code=process.returncode, messages=messages, raw_output=raw_output
        )

        return result

    except Exception as e:
        result = PylintResult(
            return_code=1,
            messages=[],
            error=f"Error running pylint: {str(e)}",
            raw_output=None,
        )
        return result


def get_direct_instruction_for_pylint_code(code: str) -> Optional[str]:
    """
    Provides a direct instruction for a given Pylint code.

    Args:
        code: The Pylint code (e.g., "R0902", "C0411", "W0612").

    Returns:
        A direct instruction string or None if the code is not recognized.
    """
    instructions = {
        "R0902": "Refactor the class by breaking it into smaller classes or using data structures to reduce the number of instance attributes.",  # too-many-instance-attributes
        "C0411": "Organize your imports into three groups: standard library imports, third-party library imports, and local application/project imports, separated by blank lines, with each group sorted alphabetically.",  # wrong-import-order
        "W0612": "Either use the variable or remove the variable assignment if it is not needed.",  # unused-variable
        "W0621": "Avoid shadowing variables from outer scopes.",  # redefined-outer-name
        "W0311": "Ensure consistent indentation using 4 spaces for each level of nesting.",  # bad-indentation
        "W0718": "Explicitly catch only the specific exceptions you expect and handle them appropriately, rather than using a bare `except:` clause.",  # broad-exception-caught
        "E0601": "Ensure a variable is assigned a value before it is used within its scope.",  # used-before-assignment
        "E0602": "Before using a variable, ensure it is either defined within the current scope (e.g., function, class, or global) or imported correctly from a module.",  # undefined-variable
        "E1120": "Provide a value for each parameter in the function call that doesn't have a default value.",  # no-value-for-parameter
        "E0401": "Verify that the module or package you are trying to import is installed and accessible in your Python environment, and that the import statement matches its name and location.",  # import-error
        "E0611": "Verify that the name you are trying to import (e.g., function, class, variable) actually exists within the specified module or submodule and that the spelling is correct.",  # no-name-in-module
        "W4903": "Replace the deprecated argument with its recommended alternative; consult the documentation for the function or method to identify the correct replacement.",  # deprecated-argument
        "W1203": "Use string formatting with the `%` operator or `.format()` method when passing variables to logging functions instead of f-strings; for example, `logging.info('Value: %s', my_variable)` or `logging.info('Value: {}'.format(my_variable))`",  # logging-fstring-interpolation
        "W0613": "Remove the unused argument from the function definition if it is not needed, or if it is needed for compatibility or future use, use `_` as the argument's name to indicate it's intentionally unused, or use it within the function logic.",  # unused-argument
        "C0415": "Move the import statement to the beginning of the file, outside of any conditional blocks, functions, or classes; all imports should be at the top of the file.",  # import-outside-toplevel
        "E0704": "Ensure that a `raise` statement without an exception object or exception type only appears inside an `except` block; it should re-raise the exception that was caught, not be used outside of an exception handling context.",  # misplaced-bare-raise
        "E0001": "Carefully review the indicated line (and potentially nearby lines) for syntax errors such as typos, mismatched parentheses/brackets/quotes, invalid operators, or incorrect use of keywords; consult the Python syntax rules to correct the issue.",  # syntax-error
        "R0911": "Refactor the function to reduce the number of return statements, potentially by simplifying the logic or using helper functions.",  # too-many-return-statements
        "W0707": "When raising a new exception inside an except block, use raise ... from original_exception to preserve the original exception's traceback.",  # raise-missing-from
        "E1125": "Fix the function call by using keyword arguments for parameters that are defined as keyword-only in the function signature. Use the parameter name as a keyword when passing the value.",  # missing-kwoa
        "E1101": "Define the missing attribute or method directly in the class declaration. If the attribute or method should be inherited from a parent class, ensure that the parent class is correctly specified in the class definition.",  # no-member
        "E0213": "Ensure the first parameter of instance methods in a class is named 'self'. This parameter represents the instance of the class and is automatically passed when calling the method on an instance.",  # no-self-argument
        "E1123": "Make sure to only use keyword arguments that are defined in the function or method definition you're calling.",  # unexpected-keyword-argument
    }

    return instructions.get(code)


def run_pylint_check(
    project_dir: str,
    categories: Optional[Set[PylintMessageType]] = None,
    disable_codes: Optional[List[str]] = None,
    python_executable: Optional[str] = None,
) -> PylintResult:
    """
    Run pylint check on a project directory and returns the result.

    Args:
        project_dir: The path to the project directory to analyze.
        categories: Set of specific pylint categories to filter by. Available categories are:
            - PylintMessageType.CONVENTION: Style conventions (C)
            - PylintMessageType.REFACTOR: Refactoring suggestions (R)
            - PylintMessageType.WARNING: Python-specific warnings (W)
            - PylintMessageType.ERROR: Probable bugs in the code (E)
            - PylintMessageType.FATAL: Critical errors that prevent pylint from working (F)
            Defaults to {ERROR, FATAL} if None.
        disable_codes: Optional list of pylint codes to disable during analysis. Common codes include:
            - C0114: Missing module docstring
            - C0116: Missing function docstring
            - C0301: Line too long
            - C0303: Trailing whitespace
            - C0305: Trailing newlines
            - W0311: Bad indentation
            - W0611: Unused import
            - W1514: Unspecified encoding
        python_executable: Optional path to Python interpreter to use for running tests. If None, defaults to sys.executable.

    Returns:
        PylintResult with the analysis outcome.
    """
    # Default disable codes if none provided
    if disable_codes is None:
        disable_codes = [
            # not required for now
            "C0114",  # doc missing
            "C0116",  # doc missing
            #
            # can be solved with formatting / black
            "C0301",  # line-too-long
            "C0303",  # trailing-whitespace
            "C0305",  # trailing-newlines
            "W0311",  # bad-indentation   - instruction available
            #
            # can be solved with iSort
            "W0611",  # unused-import
            "W1514",  # unspecified-encoding
        ]

    return get_pylint_results(
        project_dir, disable_codes=disable_codes, python_executable=python_executable
    )


def get_pylint_prompt(
    project_dir: str,
    categories: Optional[Set[PylintMessageType]] = None,
    disable_codes: Optional[List[str]] = None,
    python_executable: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a prompt for fixing pylint issues based on the analysis of a project.

    Args:
        project_dir: The path to the project directory to analyze.
        categories: Set of specific pylint categories to filter by. Available categories are:
            - PylintMessageType.CONVENTION: Style conventions (C)
            - PylintMessageType.REFACTOR: Refactoring suggestions (R)
            - PylintMessageType.WARNING: Python-specific warnings (W)
            - PylintMessageType.ERROR: Probable bugs in the code (E)
            - PylintMessageType.FATAL: Critical errors that prevent pylint from working (F)
            Defaults to {ERROR, FATAL} if None.
        disable_codes: Optional list of pylint codes to disable during analysis. Common codes include:
            - C0114: Missing module docstring
            - C0116: Missing function docstring
            - C0301: Line too long
            - C0303: Trailing whitespace
            - C0305: Trailing newlines
            - W0311: Bad indentation
            - W0611: Unused import
            - W1514: Unspecified encoding
        python_executable: Optional path to Python interpreter to use for running tests. If None, defaults to sys.executable.

    Returns:
        A prompt string with issue details and instructions, or None if no issues were found.
    """
    # Use default categories if none provided
    if categories is None:
        categories = DEFAULT_CATEGORIES

    # Default disable codes if none provided
    if disable_codes is None:
        disable_codes = [
            # not required for now
            "C0114",  # doc missing
            "C0116",  # doc missing
            #
            # can be solved with formatting / black
            "C0301",  # line-too-long
            "C0303",  # trailing-whitespace
            "C0305",  # trailing-newlines
            "W0311",  # bad-indentation   - instruction available
            #
            # can be solved with iSort
            "W0611",  # unused-import
            "W1514",  # unspecified-encoding
        ]

    pylint_results = get_pylint_results(
        project_dir, disable_codes=disable_codes, python_executable=python_executable
    )

    codes = pylint_results.get_message_ids()
    if len(categories) > 0:
        codes = filter_pylint_codes_by_category(codes, categories=categories)

    if len(codes) > 0:
        code = list(codes)[0]
        prompt = get_prompt_for_known_pylint_code(code, project_dir, pylint_results)
        if prompt is not None:
            return prompt
        else:
            prompt = get_prompt_for_unknown_pylint_code(
                code, project_dir=project_dir, pylint_results=pylint_results
            )
            return prompt  # just for the first code
    else:
        return None


def get_prompt_for_known_pylint_code(
    code: str, project_dir: str, pylint_results: PylintResult
) -> Optional[str]:
    """
    Generate a prompt for a known pylint code with instructions and details.

    Args:
        code: The pylint code (e.g., "E0602")
        project_dir: The project directory path
        pylint_results: The pylint analysis results

    Returns:
        A formatted prompt string or None if no instruction is found for the code
    """
    instruction = get_direct_instruction_for_pylint_code(code)
    if not instruction:
        return None

    pylint_results_filtered = pylint_results.get_messages_filtered_by_message_id(code)
    details_lines = []

    for message in pylint_results_filtered:
        path = normalize_path(message.path, project_dir)
        # Create a dictionary and dump the entire structure
        issue_dict = {
            "module": message.module,
            "obj": message.obj,
            "line": message.line,
            "column": message.column,
            "path": path,
            "message": message.message,
        }
        # Get JSON string for the whole object and add comma for the list format
        details_lines.append(json.dumps(issue_dict, indent=4) + ",")

    details_str = "\n".join(details_lines)
    query = f"""pylint found some issues related to code {code}.
    {instruction}
    Please consider especially the following locations in the source code:
    {details_str}"""
    return query


def get_prompt_for_unknown_pylint_code(
    code: str, project_dir: str, pylint_results: PylintResult
) -> str:
    """
    Generate a prompt for an unknown pylint code with issue details.

    Args:
        code: The pylint code (e.g., "E0602")
        project_dir: The project directory path
        pylint_results: The pylint analysis results

    Returns:
        A formatted prompt string requesting instructions for this code
    """
    pylint_results_filtered = pylint_results.get_messages_filtered_by_message_id(code)

    first_result = next(iter(pylint_results_filtered))
    symbol = first_result.symbol

    details_lines = []
    for message in pylint_results_filtered:
        path = normalize_path(message.path, project_dir)
        # Create a dictionary and dump the entire structure
        issue_dict = {
            "module": message.module,
            "obj": message.obj,
            "line": message.line,
            "column": message.column,
            "path": path,
            "message": message.message,
        }
        # Get JSON string for the whole object and add comma for the list format
        details_lines.append(json.dumps(issue_dict, indent=4) + ",")

    # Store the entire details section in a variable first
    details_str = "\n".join(details_lines)

    query = f"""pylint found some issues related to code {code} / symbol {symbol}.
    
    Please do two things:
    1. Please provide 1 direct instruction on how to fix pylint code "{code}" ({symbol}) in the general comment of the response.
    
    2. Please apply that instruction   
    Please consider especially the following locations in the source code:
    {details_str}"""
    return query
