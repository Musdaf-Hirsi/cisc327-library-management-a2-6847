"""
Services-layer Library Service - copy of business logic adapted for services package.
Includes payment-related functions to be tested with mocks/stubs.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    get_patron_borrowed_books,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books
)


def _as_date(d):
    if d is None:
        return None
    # Accept date or datetime objects directly
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).date()
        except ValueError:
            pass
    return None


def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
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
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."

    current_borrowed = get_patron_borrow_count(patron_id)
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."

    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)

    if not insert_borrow_record(patron_id, book_id, borrow_date, due_date):
        return False, "Database error occurred while creating borrow record."
    if not update_book_availability(book_id, -1):
        return False, "Database error occurred while updating book availability."

    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}. '


def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
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
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "Invalid patron ID"}

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

    fee_amount = round(days_overdue * 0.5, 2)
    return {"fee_amount": fee_amount, "days_overdue": days_overdue, "status": "OVERDUE"}


def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
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


# --------------------------
# Payment-related functions
# --------------------------
def pay_late_fees(patron_id: str, book_id: int, payment_gateway) -> Dict:
    """Process payment for late fees for a single book.

    payment_gateway must implement process_payment(amount) -> dict with keys: success (bool), transaction_id (str)
    """
    # Validate patron / fee
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    if fee_info.get('status') == 'Invalid patron ID':
        return {'success': False, 'message': 'Invalid patron ID'}
    amount = float(fee_info.get('fee_amount', 0.0))
    if amount <= 0:
        return {'success': False, 'message': 'No fees due'}

    try:
        res = payment_gateway.process_payment(amount)
    except Exception as e:
        return {'success': False, 'message': f'Payment gateway error: {e}'}

    if not res or not res.get('success'):
        return {'success': False, 'message': 'Payment declined'}

    # on success, we could mark payment in DB (omitted) and return tx id
    return {'success': True, 'transaction_id': res.get('transaction_id')}


def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway) -> Dict:
    """Request refund via payment gateway.

    Validations: transaction_id non-empty, amount > 0 and <= 15
    """
    if not transaction_id or not isinstance(transaction_id, str):
        return {'success': False, 'message': 'Invalid transaction ID'}
    try:
        amount = float(amount)
    except Exception:
        return {'success': False, 'message': 'Invalid amount'}
    if amount <= 0 or amount > 15:
        return {'success': False, 'message': 'Invalid refund amount'}

    try:
        res = payment_gateway.refund_payment(transaction_id, amount)
    except Exception as e:
        return {'success': False, 'message': f'Gateway error: {e}'}

    if not res or not res.get('success'):
        return {'success': False, 'message': 'Refund rejected'}

    return {'success': True, 'refund_id': res.get('refund_id')}
