# tests/test_library_service.py
import pytest
from datetime import date, timedelta
import library_service


# ------------------------
# R1: Add Book
# ------------------------

def test_add_book_invalid_isbn():
    success, message = library_service.add_book_to_catalog("Test", "Author", "123", 2)
    assert success is False
    assert "isbn" in message.lower()

def test_add_book_empty_title():
    success, message = library_service.add_book_to_catalog("", "Author", "1234567890123", 2)
    assert success is False
    assert "title is required" in message.lower()

def test_add_book_long_author():
    long_name = "A" * 101
    success, message = library_service.add_book_to_catalog("Book", long_name, "1234567890123", 2)
    assert success is False
    assert "author must be less than 100" in message.lower()

def test_add_book_invalid_copies():
    success, message = library_service.add_book_to_catalog("Book", "Author", "1234567890123", 0)
    assert success is False
    assert "total copies" in message.lower()


# ------------------------
# R2: Borrow Book
# ------------------------

def test_borrow_book_invalid_patron():
    success, message = library_service.borrow_book_by_patron("12", 1)  # too short
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_book_nonexistent_book(monkeypatch):
    # Force DB to return no book for this ID
    monkeypatch.setattr(library_service, "get_book_by_id", lambda _id: None, raising=False)
    success, message = library_service.borrow_book_by_patron("123456", 9999)
    assert success is False
    assert "book not found" in message.lower()

def test_borrow_book_empty_patron():
    success, message = library_service.borrow_book_by_patron("", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_book_invalid_format():
    success, message = library_service.borrow_book_by_patron("abcdef", 1)  # not digits
    assert success is False
    assert "invalid patron id" in message.lower()


# ------------------------
# R3: Return Book
# ------------------------

def test_return_book_no_active_record(monkeypatch):
    # Simulate: no active borrow record to update
    monkeypatch.setattr(
        library_service, "update_borrow_record_return_date",
        lambda patron_id, book_id, now: False,
        raising=False
    )
    success, message = library_service.return_book_by_patron("123456", 1)
    assert success is False
    assert "no active borrow record" in message.lower()

def test_return_book_invalid_patron():
    success, message = library_service.return_book_by_patron("12", 1)
    assert success is False
    assert "invalid patron id" in message.lower()


# ------------------------
# R4: Late Fee
# ------------------------

def test_late_fee_no_active_borrow(monkeypatch):
    # Patron has no active records
    monkeypatch.setattr(library_service, "get_patron_borrowed_books", lambda pid: [], raising=False)
    result = library_service.calculate_late_fee_for_book("123456", 1)
    assert isinstance(result, dict)
    assert result.get("status") == "No active borrow record found"
    assert result.get("fee_amount") == 0.0
    assert result.get("days_overdue") == 0

def test_late_fee_invalid_book_id(monkeypatch):
    # Patron has a record, but for a different book_id
    monkeypatch.setattr(
        library_service,
        "get_patron_borrowed_books",
        lambda pid: [{"book_id": 9999, "due_date": date.today()}],
        raising=False
    )
    result = library_service.calculate_late_fee_for_book("123456", 1)
    assert result.get("status") == "No active borrow record found"
    assert result.get("fee_amount") == 0.0
    assert result.get("days_overdue") == 0

def test_late_fee_overdue(monkeypatch):
    overdue_due = date.today() - timedelta(days=3)
    monkeypatch.setattr(
        library_service,
        "get_patron_borrowed_books",
        lambda pid: [{"book_id": 1, "due_date": overdue_due}],
        raising=False
    )
    result = library_service.calculate_late_fee_for_book("123456", 1)
    assert result["status"] == "OVERDUE"
    assert result["days_overdue"] == 3
    assert result["fee_amount"] == 1.5  # 3 * $0.50


# ------------------------
# R5: Search Books
# ------------------------

def test_search_books_returns_list(monkeypatch):
    monkeypatch.setattr(library_service, "get_all_books", lambda: [], raising=False)
    results = library_service.search_books_in_catalog("anything", "title")
    assert isinstance(results, list)

def test_search_books_empty_string(monkeypatch):
    monkeypatch.setattr(library_service, "get_all_books", lambda: [], raising=False)
    results = library_service.search_books_in_catalog("", "title")
    assert isinstance(results, list)
    assert results == []

def test_search_books_by_title_filters(monkeypatch):
    sample = [
        {"title": "Python 101", "author": "A", "isbn": "1"},
        {"title": "Flask in Action", "author": "B", "isbn": "2"},
    ]
    monkeypatch.setattr(library_service, "get_all_books", lambda: sample, raising=False)
    results = library_service.search_books_in_catalog("flask", "title")
    assert len(results) == 1
    assert results[0]["title"] == "Flask in Action"

def test_search_books_by_author_filters(monkeypatch):
    sample = [
        {"title": "X", "author": "Alice", "isbn": "1"},
        {"title": "Y", "author": "Bob", "isbn": "2"},
    ]
    monkeypatch.setattr(library_service, "get_all_books", lambda: sample, raising=False)
    results = library_service.search_books_in_catalog("bob", "author")
    assert len(results) == 1
    assert results[0]["author"] == "Bob"


# ------------------------
# R6: Catalog List (helper present)
# ------------------------

def test_catalog_list_function_exists():
    assert hasattr(library_service, "get_all_books")

def test_catalog_list_returns_list(monkeypatch):
    monkeypatch.setattr(library_service, "get_all_books", lambda: [], raising=False)
    books = library_service.get_all_books()
    assert isinstance(books, list)


# ------------------------
# R7: Patron Status Report
# ------------------------

def test_patron_status_report_valid(monkeypatch):
    # one borrowed book, not overdue
    borrow_list = [{
        "book_id": 7,
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "borrow_date": date.today() - timedelta(days=1),
        "due_date": date.today() + timedelta(days=13),
        "is_overdue": False,
    }]
    monkeypatch.setattr(library_service, "get_patron_borrowed_books", lambda pid: borrow_list, raising=False)

    result = library_service.get_patron_status_report("123456")
    assert isinstance(result, dict)
    assert result.get("patron_id") == "123456"
    assert isinstance(result.get("currently_borrowed"), list)
    assert result.get("total_active") == 1
    assert result.get("overdue_count") == 0
    assert result.get("status") in {"OK", "No active borrows"}

def test_patron_status_report_invalid_id():
    result = library_service.get_patron_status_report("12")
    assert result == {}
