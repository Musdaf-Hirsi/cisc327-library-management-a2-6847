"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    get_patron_borrowed_books,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books
)

def _as_date(d):
    if d is None:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # try ISO first
        try:
            return datetime.fromisoformat(d).date()
        except ValueError:
            pass
        # fallback: YYYY-MM-DD
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog. (R1)
    """
    if not title or not title.strip():
        return False, "Title is required."
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    if not author or not author.strip():
        return False, "Author is required."
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."

    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."

    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Borrow a book. (R2)
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."

    current_borrowed = get_patron_borrow_count(patron_id)
    if current_borrowed >= 5:  # <=— changed from > 5
        return False, "You have reached the maximum borrowing limit of 5 books."

    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)

    if not insert_borrow_record(patron_id, book_id, borrow_date, due_date):
        return False, "Database error occurred while creating borrow record."
    if not update_book_availability(book_id, -1):
        return False, "Database error occurred while updating book availability."

    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Return a borrowed book. (R3)
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    now = datetime.now()
    updated = update_borrow_record_return_date(patron_id, book_id, now)
    if not updated:
        return False, "No active borrow record found for this patron/book."

    if not update_book_availability(book_id, +1):
        return False, "Database error updating availability."

    return True, "Book returned successfully."

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book. (R4)
    Currently a placeholder; implement when borrow record access is available.
    """
    # Validate patron id
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "Invalid patron ID"}

    # Look for active borrow for this patron and book
    borrowed = get_patron_borrowed_books(patron_id)
    record = next((r for r in borrowed if r.get('book_id') == book_id), None)
    if not record:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "No active borrow record found"}

    due_raw = record.get('due_date')
    due = _as_date(due_raw)
    if not due:
     return {"fee_amount": 0.0, "days_overdue": 0, "status": "No due date available"}

    today = datetime.now().date()
    days_overdue = (today - due).days

    if days_overdue <= 0:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "OK"}

    # Fee policy: $0.50 per day overdue
    fee_amount = round(days_overdue * 0.5, 2)
    return {"fee_amount": fee_amount, "days_overdue": days_overdue, "status": "OVERDUE"}

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search catalog by title/author/isbn. (R5)
    """
    term = (search_term or "").strip().lower()
    if not term:
        return []

    books = get_all_books() or []
    if search_type not in {"title", "author", "isbn"}:
        search_type = "title"

    out = []
    for b in books:
        val = str(b.get(search_type, "")).lower()
        if term in val:
            out.append(b)
    return out

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Patron status report placeholder. (R7)
    """
    # Validate patron id
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {}

    borrowed = get_patron_borrowed_books(patron_id)
    currently_borrowed = []
    overdue_count = 0
    for r in borrowed:
        is_overdue = bool(r.get('is_overdue'))
        if is_overdue:
            overdue_count += 1
        currently_borrowed.append({
            'book_id': r.get('book_id'),
            'title': r.get('title'),
            'author': r.get('author'),
            'borrow_date': r.get('borrow_date').isoformat() if r.get('borrow_date') else None,
            'due_date': r.get('due_date').isoformat() if r.get('due_date') else None,
            'is_overdue': is_overdue
        })

    total_active = len(currently_borrowed)
    status = 'OK' if total_active > 0 else 'No active borrows'
    return {
        'patron_id': patron_id,
        'currently_borrowed': currently_borrowed,
        'total_active': total_active,
        'overdue_count': overdue_count,
        'status': status
    }
