def test_a1_pass():
    assert 1 == 1


def test_a2_pass():
    assert "hello" == "hello"


def test_a3_pass():
    assert [1, 2, 3] == [1, 2, 3]


def test_a4_fail():
    print("Debug: test_a4_fail executing")
    assert 1 == 2  # Fail


def test_a5_fail():
    print("Debug: test_a5_fail processing data")
    data = [1, 2, 3]
    print(f"Debug: data is {data}")
    assert len(data) == 5  # Fail
