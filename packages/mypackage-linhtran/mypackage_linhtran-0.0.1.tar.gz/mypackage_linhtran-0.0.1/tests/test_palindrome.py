from palindrome import is_palindrome

def test_paline():
    assert is_palindrome("sts") == True
    
def test_not_paline():
    assert is_palindrome("str") == False

def test_empty_paline():
    assert is_palindrome("") == True