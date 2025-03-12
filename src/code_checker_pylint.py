import logging
import os
import subprocess
import sys
from enum import Enum
from typing import NamedTuple, Optional, Set

logger = logging.getLogger(__name__)


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
    messages: list[PylintMessage]
    error: Optional[str] = None  # Capture any execution errors
    raw_output: Optional[str] = None  # Capture raw output from pylint

    def get_message_ids(self) -> set[str]:
        """Returns a set of all unique message IDs."""
        return {message.message_id for message in self.messages}

    def get_messages_filtered_by_message_id(self, message_id: str) -> list[PylintMessage]:
        """Returns a list of messages filtered by the given message ID."""
        return [message for message in self.messages if message.message_id == message_id]


# actually, this seems to be the PylintMessage.type - could be refactored
class PylintCategory(Enum):
    """Categories for Pylint codes."""

    CONVENTION = "convention"
    REFACTOR = "refactor"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


def filter_pylint_codes_by_category(
    pylint_codes: Set[str],
    categories: Set[PylintCategory],
) -> Set[str]:
    """Filters Pylint codes based on the specified categories.

    Args:
        pylint_codes: A set of Pylint codes (e.g., {"C0301", "R0201", "W0613", "E0602", "F0001"}).
        categories: A set of PylintCategory enums to filter by (e.g., {PylintCategory.ERROR, PylintCategory.FATAL}).

    Returns:
        A set of Pylint codes that match the specified categories.
    """
    category_prefixes = {
        PylintCategory.CONVENTION: "C",
        PylintCategory.REFACTOR: "R",
        PylintCategory.WARNING: "W",
        PylintCategory.ERROR: "E",
        PylintCategory.FATAL: "F",
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
    disable_codes: list[str] | None = None,
) -> PylintResult:
    """Runs pylint on the specified project directory and returns the results.

    Args:
        project_dir: The path to the project directory.
        disable_codes: the codes that are not

    Returns:
        A PylintResult object containing the results of the pylint run.

    Raises:
        FileNotFoundError: If the project directory does not exist.
    """

    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    try:
        # Determine the Python executable from the current environment
        python_executable = sys.executable

        # Construct the pylint command
        pylint_command = [
            python_executable,
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
        logger.debug(" ".join(pylint_command))
        process = subprocess.run(
            pylint_command, cwd=project_dir, capture_output=True, text=True, check=False
        )

        raw_output = process.stdout

        # Parse pylint output from JSON, if available
        messages: list[PylintMessage] = []

        import json

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
            return PylintResult(
                return_code=process.returncode,
                messages=[],
                error=f"Pylint output parsing failed: {e}",
                raw_output=raw_output,
            )

        return PylintResult(
            return_code=process.returncode, messages=messages, raw_output=raw_output
        )

    except Exception as e:
        return PylintResult(return_code=1, messages=[], error=str(e), raw_output=None)


def get_pylint_results_as_str(result: PylintResult, remove_project_dir: str) -> str:
    """Render Pylint results in a user-friendly format as str."""
    list_result: list[str] = []
    if result.error:
        list_result.append(f"Pylint Error: {result.error}")
        if result.raw_output:
            list_result.append("Raw output from pylint:")
            result_raw_output = result.raw_output
            result_raw_output = result_raw_output.replace(remove_project_dir + "\\", "")
            list_result.append(result_raw_output)
    elif result.return_code == 0:
        list_result.append("Pylint found no issues.")
    else:
        list_result.append("Pylint found the following issues:")
        for message in result.messages:
            message_path = message.path
            message_path = message_path.replace(remove_project_dir + "\\", "")
            list_result.append(
                f"{message_path}:{message.line}:{message.column}: {message.symbol} "
                f"({message.message_id}) {message.message}"
            )
    str_result = "\n".join(list_result)
    return str_result


# prompt:
# Please provide 1 direct instruction for pylint code "E1120" ( no-value-for-parameter  )


def get_direct_instruction_for_pylint_code(code: str) -> str | None:
    """
    Provides a direct instruction for a given Pylint code.

    Args:
        code: The Pylint code (e.g., "R0902", "C0411", "W0612").

    Returns:
        A direct instruction string or None if the code is not recognized.
    """
    if code == "R0902":  # too-many-instance-attributes
        return "Refactor the class by breaking it into smaller classes or using data structures to reduce the number of instance attributes."
    elif code == "C0411":  # wrong-import-order
        return "Organize your imports into three groups: standard library imports, third-party library imports, and local application/project imports, separated by blank lines, with each group sorted alphabetically."
    elif code == "W0612":  # unused-variable
        return "Either use the variable or remove the variable assignment if it is not needed."
    elif code == "W0621":  # redefined-outer-name
        return "Avoid shadowing variables from outer scopes."
    elif code == "W0311":  # bad-indentation
        return "Ensure consistent indentation using 4 spaces for each level of nesting."
    elif code == "W0718":  # broad-exception-caught
        return "Explicitly catch only the specific exceptions you expect and handle them appropriately, rather than using a bare `except:` clause."
    elif code == "E0601":  # used-before-assignment
        return "Ensure a variable is assigned a value before it is used within its scope."
    elif code == "E0602":  # undefined-variable
        return "Before using a variable, ensure it is either defined within the current scope (e.g., function, class, or global) or imported correctly from a module."
    elif code == "E1120":  # no-value-for-parameter
        return "Provide a value for each parameter in the function call that doesn't have a default value."
    elif code == "E0401":  # import-error
        return "Verify that the module or package you are trying to import is installed and accessible in your Python environment, and that the import statement matches its name and location."
    elif code == "E0611":  # no-name-in-module
        return "Verify that the name you are trying to import (e.g., function, class, variable) actually exists within the specified module or submodule and that the spelling is correct."
    elif code == "W4903":  # deprecated-argument
        return "Replace the deprecated argument with its recommended alternative; consult the documentation for the function or method to identify the correct replacement."
    elif code == "W1203":  # logging-fstring-interpolation
        return "Use string formatting with the `%` operator or `.format()` method when passing variables to logging functions instead of f-strings; for example, `logging.info('Value: %s', my_variable)` or `logging.info('Value: {}'.format(my_variable))`"
    elif code == "W0613":  # unused-argument
        return "Remove the unused argument from the function definition if it is not needed, or if it is needed for compatibility or future use, use `_` as the argument's name to indicate it's intentionally unused, or use it within the function logic."
    elif code == "C0415":  # import-outside-toplevel
        return "Move the import statement to the beginning of the file, outside of any conditional blocks, functions, or classes; all imports should be at the top of the file."
    elif code == "E0704":  # misplaced-bare-raise
        return "Ensure that a `raise` statement without an exception object or exception type only appears inside an `except` block; it should re-raise the exception that was caught, not be used outside of an exception handling context."
    elif code == "E0001":  # syntax-error
        return "Carefully review the indicated line (and potentially nearby lines) for syntax errors such as typos, mismatched parentheses/brackets/quotes, invalid operators, or incorrect use of keywords; consult the Python syntax rules to correct the issue."
    elif code == "R0911":  # too-many-return-statements
        return "Refactor the function to reduce the number of return statements, potentially by simplifying the logic or using helper functions."
    elif code == "W0707":  # raise-missing-from
        return "When raising a new exception inside an except block, use raise ... from original_exception to preserve the original exception's traceback."
    elif code == "E1125":  # missing-kwoa
        return "Fix the function call by using keyword arguments for parameters that are defined as keyword-only in the function signature. Use the parameter name as a keyword when passing the value."
    elif code == "E1101":  # no-member
        return "Define the missing attribute or method directly in the class declaration. If the attribute or method should be inherited from a parent class, ensure that the parent class is correctly specified in the class definition."
    elif code == "E0213":  # no-self-argument
        return "Ensure the first parameter of instance methods in a class is named 'self'. This parameter represents the instance of the class and is automatically passed when calling the method on an instance."
    elif code == "E1123":  # unexpected-keyword-argument
        return "Make sure to only use keyword arguments that are defined in the function or method definition you're calling."
    else:
        return None


def get_pylint_prompt(
    project_dir: str,
    categories: Set[PylintCategory] | None = None,
    pytest_project_marker: str | None = None,
) -> str | None:
    # prompt within existing chat where all python files are known
    # enhancement ideas
    # - check for errors, check later for warnings
    # - extend get_direct_instruction_for_pylint_code() dynamically, store instructions

    if categories is None:
        categories = set()

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
    pylint_results = get_pylint_results(project_dir, disable_codes=disable_codes)

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


def get_prompt_for_known_pylint_code(code, project_dir, pylint_results):
    instruction = get_direct_instruction_for_pylint_code(code)
    pylint_results_filtered = pylint_results.get_messages_filtered_by_message_id(code)
    details_lines = []
    for message in pylint_results_filtered:
        message: PylintMessage
        path = message.path
        path = path.replace(project_dir + "\\", "")
        details_line = f"""{{
        "module": "{message.module}",
        "obj": "{message.obj}",
        "line": {message.line},
        "column": {message.column},
        "path": "{path}",
        "message": "{message.message}",
    
    }},"""

        #   "type": "{message.type}",
        #   "symbol": "{message.symbol}",
        #   "message-id": "{message.message_id}"

        details_lines.append(details_line)
    query = f"""pylint found some issues related to code {code}.
    {instruction}
    Please consider especially the following locations in the source code:
    {'\n'.join(details_lines)}"""
    return query


def get_prompt_for_unknown_pylint_code(code, project_dir, pylint_results):
    pylint_results_filtered = pylint_results.get_messages_filtered_by_message_id(code)

    first_result = next(iter(pylint_results_filtered))
    symbol = first_result.symbol

    details_lines = []
    for message in pylint_results_filtered:
        message: PylintMessage
        path = message.path
        path = path.replace(project_dir + "\\", "")
        details_line = f"""{{
        "module": "{message.module}",
        "obj": "{message.obj}",
        "line": {message.line},
        "column": {message.column},
        "path": "{path}",
        "message": "{message.message}",

    }},"""

        #   "type": "{message.type}",
        #   "symbol": "{message.symbol}",
        #   "message-id": "{message.message_id}"

        details_lines.append(details_line)
    query = f"""pylint found some issues related to code {code} / symbol {symbol}.
    
    Please do two things:
    1. Please provide 1 direct instruction on how to fix pylint code "{code}" ( {symbol} ) in the general comment of the response.
    
    2. Please apply that instruction   
    Please consider especially the following locations in the source code:
    {'\n'.join(details_lines)}"""
    return query
