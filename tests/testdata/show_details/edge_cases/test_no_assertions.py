# This will cause collection errors
import non_existent_module

def test_with_import_error():
    non_existent_module.do_something()
    assert True
    
def test_syntax_error():
    # Intentional syntax error
    if True
        assert True
