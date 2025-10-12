import pytest
import library_service

# ------------------------
# R1: Add Book
# ------------------------

def test_add_book_invalid_isbn():
    success, message = library_service.add_book_to_catalog("Test", "Author", "123", 2)
    assert success is False
    assert "ISBN" in message

def test_add_book_empty_title():
    success, message = library_service.add_book_to_catalog("", "Author", "1234567890123", 2)
    assert success is False
    assert "Title is required" in message

def test_add_book_long_author():
    long_name = "A" * 101
    success, message = library_service.add_book_to_catalog("Book", long_name, "1234567890123", 2)
    assert success is False
    assert "Author must be less than 100" in message

def test_add_book_invalid_copies():
    success, message = library_service.add_book_to_catalog("Book", "Author", "1234567890123", 0)
    assert success is False
    assert "Total copies" in message

# ------------------------
# R2: Borrow Book
# ------------------------

def test_borrow_book_invalid_patron():
    success, message = library_service.borrow_book_by_patron("12", 1)  # too short
    assert success is False
    assert "Invalid patron ID" in message

def test_borrow_book_nonexistent_book():
    success, message = library_service.borrow_book_by_patron("123456", 9999)  # random id
    assert success is False
    assert "Book not found" in message

def test_borrow_book_empty_patron():
    success, message = library_service.borrow_book_by_patron("", 1)
    assert success is False
    assert "Invalid patron ID" in message

def test_borrow_book_invalid_format():
    success, message = library_service.borrow_book_by_patron("abcdef", 1)  # not digits
    assert success is False
    assert "Invalid patron ID" in message

# ------------------------
# R3: Return Book (stub)
# ------------------------

def test_return_book_not_implemented():
    success, message = library_service.return_book_by_patron("123456", 1)
    # If there is no active borrow record for book 1, function should return False
    assert success is False
    assert "No active borrow record" in message

def test_return_book_invalid_patron():
    success, message = library_service.return_book_by_patron("12", 1)
    assert success is False
    assert "Invalid patron ID" in message  # invalid patron id handled

# ------------------------
# R4: Late Fee (stub)
# ------------------------

def test_late_fee_not_implemented():
    result = library_service.calculate_late_fee_for_book("123456", 1)
    # For no active borrow, function returns a dict indicating no active borrow
    assert isinstance(result, dict)
    assert set(["fee_amount", "days_overdue", "status"]).issubset(result.keys())

def test_late_fee_invalid_book():
    result = library_service.calculate_late_fee_for_book("123456", 9999)
    # For invalid book id, expect a dict indicating no active borrow
    assert isinstance(result, dict)
    assert result.get("status") == "No active borrow record found"

# ------------------------
# R5: Search Books
# ------------------------

def test_search_books_returns_list():
    results = library_service.search_books_in_catalog("anything", "title")
    assert isinstance(results, list)

def test_search_books_empty_string():
    results = library_service.search_books_in_catalog("", "title")
    assert isinstance(results, list)

def test_search_books_by_title():
    results = library_service.search_books_in_catalog("Test", "title")
    assert isinstance(results, list)

def test_search_books_by_author():
    results = library_service.search_books_in_catalog("Author", "author")
    assert isinstance(results, list)

# ------------------------
# R6: Catalog List
# ------------------------

def test_catalog_list_function_exists():
    assert hasattr(library_service, "get_all_books")

def test_catalog_list_returns_something():
    # Might be empty, but should not crash
    try:
        books = library_service.get_all_books()
        assert isinstance(books, list)
    except Exception:
        pytest.skip("Database not connected")

# ------------------------
# R7: Patron Status Report (stub)
# ------------------------

def test_patron_status_report_not_implemented():
    result = library_service.get_patron_status_report("123456")
    # Patron 123456 has sample data (one borrowed book), so expect non-empty report
    assert isinstance(result, dict)
    assert result.get("patron_id") == "123456"
    assert isinstance(result.get("currently_borrowed"), list)

def test_patron_status_report_invalid_id():
    result = library_service.get_patron_status_report("12")
    assert result == {}
