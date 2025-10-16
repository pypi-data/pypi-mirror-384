# palindrome.py
def is_palindrome(s: str) -> bool:
    """Kiểm tra xem một chuỗi có phải là chuỗi đối xứng hay không."""
    return s == s[::-1]