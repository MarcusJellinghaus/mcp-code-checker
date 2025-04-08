# MCP Code Checker - Cline Examples

This document provides examples of how to use the MCP Code Checker with Cline in VS Code.

## Basic Usage Examples

Once you have set up the MCP Code Checker for Cline integration, you can use it by asking Cline to perform code quality checks. Here are some example prompts and how to interpret the results.

### Example 1: Run a Pylint Check

**Prompt to Cline:**
```
Can you check my Python code for quality issues using pylint?
```

**Expected Response:**
Cline will use the MCP Code Checker to run pylint on your project and provide a summary of the results. For example:

```
I've run a pylint check on your project. Here are the issues found:

1. In file src/main.py, line 45:
   - Issue: Unused import 'subprocess' (W0611)
   - Suggestion: Remove the unused import or use it in your code.

2. In file src/server.py, line 120:
   - Issue: Line too long (92/88) (C0301)
   - Suggestion: Break this line into multiple lines to improve readability.

3. In file tests/test_server_params.py, line 25:
   - Issue: Missing function docstring (C0116)
   - Suggestion: Add a docstring to describe what this function does.

Would you like me to help fix any of these issues?
```

### Example 2: Run a Pytest Check

**Prompt to Cline:**
```
Can you run my Python tests and tell me if there are any failures?
```

**Expected Response:**
Cline will use the MCP Code Checker to run pytest on your project and provide a summary of the results. For example:

```
I've run your tests using pytest. Here are the results:

✅ 15 tests passed successfully.

❌ 2 tests failed:

1. test_invalid_params in tests/test_server_params.py:
   - Error: AssertionError: Expected ValueError but got TypeError
   - Traceback: 
     tests/test_server_params.py:48: in test_invalid_params
       with pytest.raises(ValueError):
     E       AssertionError: Expected ValueError but got TypeError
   - Suggestion: The function is raising TypeError instead of ValueError. Check the validation logic in the function being tested.

2. test_parse_results in tests/test_code_checker/test_parsers.py:
   - Error: KeyError: 'summary'
   - Traceback:
     tests/test_code_checker/test_parsers.py:32: in test_parse_results
       result = parse_test_results(test_output)
     src/code_checker_pytest/parsers.py:45: in parse_test_results
       summary = test_output['summary']
     E       KeyError: 'summary'
   - Suggestion: The test_output dictionary doesn't have a 'summary' key. Check the structure of the test_output or update the parse_test_results function to handle missing keys.

Would you like me to help fix these failing tests?
```

### Example 3: Run All Checks

**Prompt to Cline:**
```
Can you perform a complete code quality analysis on my Python project?
```

**Expected Response:**
Cline will use the MCP Code Checker to run both pylint and pytest on your project and provide a comprehensive summary of the results. For example:

```
I've performed a complete code quality analysis on your project. Here are the results:

## Pylint Results:

Found 5 issues:
1. In file src/main.py, line 45:
   - Issue: Unused import 'subprocess' (W0611)
   - Suggestion: Remove the unused import or use it in your code.

2. In file src/server.py, line 120:
   - Issue: Line too long (92/88) (C0301)
   - Suggestion: Break this line into multiple lines to improve readability.

3. In file tests/test_server_params.py, line 25:
   - Issue: Missing function docstring (C0116)
   - Suggestion: Add a docstring to describe what this function does.

4. In file src/code_checker_pytest/runners.py, line 78:
   - Issue: Too many local variables (17/15) (R0914)
   - Suggestion: Refactor this function to use fewer local variables.

5. In file src/code_checker_pytest/parsers.py, line 30:
   - Issue: Consider using dict.get for a default value (R1715)
   - Suggestion: Use dict.get('key', default_value) instead of dict['key'] to handle missing keys.

## Pytest Results:

✅ 15 tests passed successfully.

❌ 2 tests failed:

1. test_invalid_params in tests/test_server_params.py:
   - Error: AssertionError: Expected ValueError but got TypeError
   - Suggestion: The function is raising TypeError instead of ValueError. Check the validation logic in the function being tested.

2. test_parse_results in tests/test_code_checker/test_parsers.py:
   - Error: KeyError: 'summary'
   - Suggestion: The test_output dictionary doesn't have a 'summary' key. Check the structure of the test_output or update the parse_test_results function to handle missing keys.

Would you like me to help fix any of these issues or failing tests?
```

## Advanced Usage Examples

### Example 4: Run Pylint with Specific Configurations

**Prompt to Cline:**
```
Can you run pylint on my project but ignore docstring warnings and line length issues?
```

**Expected Response:**
Cline will use the MCP Code Checker to run pylint with specific configurations to ignore certain types of warnings. For example:

```
I've run pylint on your project, ignoring docstring warnings (C0114, C0115, C0116) and line length issues (C0301). Here are the remaining issues:

1. In file src/main.py, line 45:
   - Issue: Unused import 'subprocess' (W0611)
   - Suggestion: Remove the unused import or use it in your code.

2. In file src/code_checker_pytest/parsers.py, line 30:
   - Issue: Consider using dict.get for a default value (R1715)
   - Suggestion: Use dict.get('key', default_value) instead of dict['key'] to handle missing keys.

Would you like me to help fix any of these issues?
```

### Example 5: Run Pytest with Specific Markers

**Prompt to Cline:**
```
Can you run only the integration tests in my project?
```

**Expected Response:**
Cline will use the MCP Code Checker to run pytest with specific markers to only run integration tests. For example:

```
I've run the integration tests in your project (tests marked with @pytest.mark.integration). Here are the results:

✅ 3 integration tests passed successfully.

❌ 1 integration test failed:

1. test_integration_with_external_api in tests/test_integration.py:
   - Error: ConnectionError: Failed to connect to external API
   - Traceback:
     tests/test_integration.py:25: in test_integration_with_external_api
       response = client.get_data()
     src/client.py:45: in get_data
       response = requests.get(self.api_url)
     E       ConnectionError: Failed to connect to external API
   - Suggestion: The test is failing because it can't connect to the external API. Make sure the API is available or consider mocking the API for testing.

Would you like me to help fix this failing test?
```

### Example 6: Fix Specific Issues

**Prompt to Cline:**
```
Can you fix the unused import in src/main.py?
```

**Expected Response:**
Cline will use the MCP Code Checker to identify the unused import and then fix it. For example:

```
I've identified an unused import in src/main.py:

Line 45: import subprocess

I'll remove this unused import for you.

✅ Fixed: Removed the unused import 'subprocess' from src/main.py.

Would you like me to check for any other issues in your code?
```

## Tips for Effective Use

1. **Be specific**: When asking Cline to check your code, be specific about what you want to check. For example, "Check my Python code for quality issues" is better than "Check my code".

2. **Use the right preset**: The MCP Code Checker supports different presets (strict, standard, minimal, debug). Choose the one that best fits your needs.

3. **Focus on specific files**: If you're only interested in checking specific files, mention them in your prompt. For example, "Check the code quality of src/main.py".

4. **Ask for explanations**: If you don't understand an issue, ask Cline to explain it. For example, "What does 'R1715' mean in the pylint results?".

5. **Request fixes**: Cline can not only identify issues but also help fix them. Just ask, "Can you fix these issues for me?".
