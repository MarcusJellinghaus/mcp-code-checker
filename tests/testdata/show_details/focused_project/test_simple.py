def test_passing():
    """A simple passing test."""
    print("Debug: test_passing started")
    result = 2 + 2
    print(f"Debug: calculation result is {result}")
    assert result == 4
    print("Debug: test_passing completed successfully")

def test_failing_with_prints():
    """A failing test that includes print statements for debugging."""
    print("Debug: processing value")
    data = {"key": "value"}
    print(f"Debug: data structure is {data}")
    
    # This will fail
    result = len(data)
    print(f"Debug: data length is {result}")
    assert result == 5  # Intentionally wrong
    print("Debug: this line should not be reached")
