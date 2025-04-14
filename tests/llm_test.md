# MCP Code Checker Test Plan

This document contains a series of independent, self-contained test modules for verifying the functionality of the MCP Code Checker server. Each module can be run individually by copying and pasting it into an LLM.

## Overview

The MCP Code Checker provides three main tools:

1. `run_pylint_check` - Runs pylint on the project code
2. `run_pytest_check` - Runs pytest on the project code
3. `run_all_checks` - Runs both pylint and pytest checks and combines the results

---

## Test Module 1: Basic Pylint Functionality

**Purpose**: Verify that the `run_pylint_check` MCP tool works correctly with various configurations.'
Use the MCP tool, report the result, do not investigate further.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment

**Test Steps**:

1. **Basic Pylint Check**
   - Call the `run_pylint_check` tool with no arguments
   - Verify that the tool returns a string response
   - Check if the response contains either "No issues found" or details about pylint issues

2. **Pylint Check with Disabled Codes**
   - Call the `run_pylint_check` tool with specific codes to disable (e.g., C0114, C0116, W0611)
   - Verify that the specified codes are not reported in the results

**Verification**:

- The tool executes without errors
- The response format is a readable string
- The content accurately reflects the state of the codebase
- Any error conditions are handled gracefully with informative messages

**Execution Approach**:

- Call the MCP tool with server name "code_checker" and tool name "run_pylint_check"
- For the second test, include a "disable_codes" parameter with an array of codes to disable

---

## Test Module 2: Basic Pytest Functionality

**Purpose**: Verify that the `run_pytest_check` tool works correctly with various configurations.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- The project contains pytest tests that can be executed

**Test Steps**:

1. **Basic Pytest Check**
   - Call the `run_pytest_check` tool with no arguments
   - Verify that the tool returns a string response
   - Check if the response contains either "All tests passed successfully" or details about failed tests

2. **Pytest Check with Markers**
   - Call the `run_pytest_check` tool with a specific marker (e.g., "unit")
   - Verify that only tests with the specified marker are executed

3. **Pytest Check with Verbosity**
   - Call the `run_pytest_check` tool with increased verbosity (e.g., level 3)
   - Verify that the output contains more detailed information

**Verification**:

- The tool executes without errors
- The response format is a readable string
- The content accurately reflects the test results
- Any error conditions are handled gracefully with informative messages

**Execution Approach**:

- Call the MCP tool with server name "code_checker" and tool name "run_pytest_check"
- For the second test, include a "markers" parameter with an array containing the marker
- For the third test, include a "verbosity" parameter with a value of 3

---

## Test Module 3: Combined Checks Functionality

**Purpose**: Verify that the `run_all_checks` tool correctly combines pylint and pytest functionality.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- The project contains code that can be analyzed by pylint and tests that can be run by pytest

**Test Steps**:

1. **Basic Combined Check**
   - Call the `run_all_checks` tool with no arguments
   - Verify that the tool returns a string response
   - Check if the response contains sections for both pylint and pytest results

2. **Combined Check with Custom Categories**
   - Call the `run_all_checks` tool with specific pylint categories (e.g., "error", "warning")
   - Verify that the pylint results include the specified categories

**Verification**:

- The tool executes without errors
- The response format is a readable string with clearly separated sections
- The content accurately reflects both pylint and pytest results
- Any error conditions are handled gracefully with informative messages

**Execution Approach**:

- Call the MCP tool with server name "code_checker" and tool name "run_all_checks"
- For the second test, include a "categories" parameter with an array of categories

---

## Test Module 4: Error Detection Capabilities

**Purpose**: Verify that the tools correctly identify and report errors in the code.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- You have permission to create temporary files in the project

**Test Steps**:

1. **Create a Python File with Pylint Errors**
   - Create a temporary file with known pylint issues (e.g., undefined variables, unused imports)
   - Run the `run_pylint_check` tool and verify that it correctly identifies the issues

2. **Create a Test File with Failing Tests**
   - Create a temporary test file with tests that are expected to fail
   - Run the `run_pytest_check` tool and verify that it correctly reports the failures

**Verification**:

- The tools correctly identify the intentional errors
- The error reports are clear and provide useful information
- The response includes specific details about the errors (file, line number, error type)

**Execution Approach**:

- Create the necessary files with errors
- Call the appropriate MCP tools to analyze them
- Verify that the errors are correctly reported

---

## Test Module 5: Edge Cases Handling

**Purpose**: Verify that the tools handle edge cases gracefully.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- You have permission to create and modify directories and files

**Test Steps**:

1. **Empty Project Directory**
   - Test the tools on an empty directory
   - Verify that they handle this case gracefully

2. **No Tests Found**
   - Test the `run_pytest_check` tool on a project with no test files
   - Verify that it handles this case appropriately

3. **Invalid Configuration**
   - Test the tools with invalid arguments (e.g., non-existent markers)
   - Verify that they provide meaningful error messages

**Verification**:

- The tools handle edge cases without crashing
- Appropriate error messages or warnings are provided
- The responses clearly indicate what the issue is

**Execution Approach**:

- Set up the necessary conditions for each edge case
- Call the appropriate MCP tools
- Verify that they handle the edge cases gracefully

---

## Test Module 6: Performance and Reliability

**Purpose**: Verify that the tools perform well and produce consistent results.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- You have access to a larger project for testing (optional)

**Test Steps**:

1. **Large Project Test**
   - Test the tools on a larger project with many files
   - Verify that they complete within a reasonable time frame

2. **Repeated Execution**
   - Run the tools multiple times in succession
   - Verify that they produce consistent results

**Verification**:

- The tools complete within a reasonable time frame
- The results are consistent across multiple executions
- There are no memory leaks or performance degradation

**Execution Approach**:

- Use a larger project if available
- Run the tools multiple times
- Compare the results for consistency

---

## Test Module 7: Integration with Different Environments

**Purpose**: Verify that the tools work correctly in different environments.

**Prerequisites**:

- The MCP Code Checker server is properly installed and configured
- You have access to the appropriate MCP tool interface for your environment
- You have access to different Python environments (optional)

**Test Steps**:

1. **Test Integration with MCP Framework**
   - Verify that the tools can be called through the MCP interface
   - Check that the results are properly formatted for consumption by an LLM

2. **Test with Different Python Environments**
   - If possible, test the tools with different Python versions or virtual environments
   - Verify that they work correctly across different environments

**Verification**:

- The tools integrate correctly with the MCP framework
- The results are properly formatted for LLM consumption
- The tools work correctly across different Python environments

**Execution Approach**:

- Test the tools in different environments if available
- Verify that they work correctly in each environment
