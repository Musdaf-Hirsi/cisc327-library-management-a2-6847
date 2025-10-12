import pytest
import library_service

# -------- tiny helper ----------
class Dummy:
    @staticmethod
    def book(
        id_=1, title="Test Title", author="Auth",
        isbn="1234567890123", total=3, available=3
    ):
        return {
            "id": id_,
            "title": title,
            "author": author,
            "isbn": isbn,
            "total_copies": total,
            "available_copies": available,
        }

# ===============================
# R1: add_book_to_catalog
# ===============================

def test_r1_add_book_success(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_isbn", lambda isbn: None)
    monkeypatch.setattr(library_service, "insert_book", lambda *a, **k: True)

    ok, msg = library_service.add_book_to_catalog(
        "Clean Code", "Robert Martin", "1234567890123", 5
    )
    assert ok is True
    assert "successfully added" in msg.lower()

def test_r1_add_book_duplicate_isbn(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_isbn",
                        lambda isbn: Dummy.book(isbn=isbn))
    ok, msg = library_service.add_book_to_catalog("Any", "Any", "1234567890123", 1)
    assert ok is False
    assert "already exists" in msg.lower()

def test_r1_add_book_requires_title():
    ok, msg = library_service.add_book_to_catalog("", "Auth", "1234567890123", 1)
    assert ok is False and "title is required" in msg.lower()

def test_r1_add_book_invalid_copies():
    ok, msg = library_service.add_book_to_catalog("Book", "Auth", "1234567890123", 0)
    assert ok is False and "total copies" in msg.lower()

# ===============================
# R2: borrow_book_by_patron
# ===============================

def test_r2_borrow_success(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_id",
                        lambda bid: Dummy.book(id_=bid, title="1984", available=2))
    monkeypatch.setattr(library_service, "get_patron_borrow_count", lambda pid: 1)
    monkeypatch.setattr(library_service, "insert_borrow_record", lambda *a, **k: True)
    monkeypatch.setattr(library_service, "update_book_availability", lambda *a, **k: True)

    ok, msg = library_service.borrow_book_by_patron("123456", 1)
    assert ok is True and "successfully borrowed" in msg.lower()

def test_r2_borrow_invalid_patron():
    ok, msg = library_service.borrow_book_by_patron("12", 1)
    assert ok is False and "invalid patron id" in msg.lower()

def test_r2_borrow_book_not_found(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_id", lambda bid: None)
    ok, msg = library_service.borrow_book_by_patron("123456", 99)
    assert ok is False and "book not found" in msg.lower()

def test_r2_borrow_unavailable(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_id",
                        lambda bid: Dummy.book(available=0))
    monkeypatch.setattr(library_service, "get_patron_borrow_count", lambda pid: 0)
    ok, msg = library_service.borrow_book_by_patron("123456", 1)
    assert ok is False and "not available" in msg.lower()

def test_r2_borrow_over_limit(monkeypatch):
    monkeypatch.setattr(library_service, "get_book_by_id",
                        lambda bid: Dummy.book(available=3))
    monkeypatch.setattr(library_service, "get_patron_borrow_count", lambda pid: 6)
    ok, msg = library_service.borrow_book_by_patron("123456", 1)
    assert ok is False and "maximum borrowing limit" in msg.lower()

# ===============================
# R3–R7: define contracts, mark xfail until implemented
# ===============================

@pytest.mark.xfail(reason="R3 return_book not implemented yet")
def test_r3_return_success_tbd():
    ok, _ = library_service.return_book_by_patron("123456", 1)
    assert ok is True

@pytest.mark.xfail(reason="R4 late fee not implemented yet")
def test_r4_late_fee_contract_tbd():
    result = library_service.calculate_late_fee_for_book("123456", 1)
    assert isinstance(result, dict)
    assert {"fee_amount", "days_overdue", "status"} <= set(result.keys())

@pytest.mark.xfail(reason="R5 search not implemented yet")
def test_r5_search_title_tbd(monkeypatch):
    monkeypatch.setattr(library_service, "get_all_books",
                        lambda: [Dummy.book(title="The Great Gatsby"),
                                 Dummy.book(title="To Kill a Mockingbird")])
    res = library_service.search_books_in_catalog("great", "title")
    assert [b["title"] for b in res] == ["The Great Gatsby"]

@pytest.mark.xfail(reason="R7 status report not implemented yet")
def test_r7_status_contract_tbd():
    r = library_service.get_patron_status_report("123456")
    assert isinstance(r, dict)
