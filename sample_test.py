import time
from library_service import add_book_to_catalog

def test_add_book_valid_input():
    """Test adding a book with valid input."""
    # 13-digit unique-ish ISBN based on time
    unique_isbn = str(int(time.time() * 1000)).ljust(13, "0")[:13]
    success, message = add_book_to_catalog("Test Book", "Test Author", unique_isbn, 5)
    assert success is True
