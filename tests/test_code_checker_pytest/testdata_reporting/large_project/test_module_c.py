def test_c1_pass():
    assert 42 == 42

def test_c2_pass():
    assert "python" == "python"

def test_c3_pass():
    assert [1, 2] + [3, 4] == [1, 2, 3, 4]

def test_c4_pass():
    assert max([1, 5, 3]) == 5

def test_c5_pass():
    assert min([1, 5, 3]) == 1

def test_c6_pass():
    assert sum([1, 2, 3]) == 6

def test_c7_pass():
    assert len("hello") == 5

def test_c8_pass():
    assert sorted([3, 1, 2]) == [1, 2, 3]
