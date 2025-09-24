def test_b1_pass():
    assert True

def test_b2_pass():
    assert 10 > 5

def test_b3_pass():
    assert "test" in "testing"

def test_b4_pass():
    assert {"a": 1}.get("a") == 1

def test_b5_pass():
    assert not False

def test_b6_fail():
    print("Debug: b6 starting")
    assert False  # Fail

def test_b7_fail():
    print("Debug: b7 calculating")
    result = 5 * 5
    print(f"Result: {result}")
    assert result == 30  # Fail

def test_b8_fail():
    print("Debug: b8 list operations")
    items = [1, 2, 3, 4]
    print(f"Items: {items}")
    assert len(items) == 10  # Fail

def test_b9_fail():
    print("Debug: b9 string operations")
    text = "hello world"
    print(f"Text: {text}")
    assert text.startswith("goodbye")  # Fail

def test_b10_fail():
    print("Debug: b10 dict operations")
    data = {"x": 1, "y": 2}
    print(f"Data: {data}")
    assert data["z"] == 3  # Fail - KeyError
