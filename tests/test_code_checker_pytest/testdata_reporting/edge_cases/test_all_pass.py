def test_simple_pass():
    print("Debug: simple test passing")
    assert True

def test_math_pass():
    print("Debug: math test")
    assert 2 + 2 == 4

def test_string_pass():
    print("Debug: string test")
    assert "hello".upper() == "HELLO"
