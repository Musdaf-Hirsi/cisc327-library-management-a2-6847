import pytest
from datetime import date, timedelta

import services.library_service as svc


def test_add_book_validation_and_success(mocker):
    # empty title
    ok, msg = svc.add_book_to_catalog('', 'A', '1234567890123', 1)
    assert not ok and 'Title is required' in msg

    # long title
    ok, msg = svc.add_book_to_catalog('A'*201, 'A', '1234567890123', 1)
    assert not ok and 'less than 200' in msg

    # invalid isbn
    ok, msg = svc.add_book_to_catalog('T', 'A', '123', 1)
    assert not ok and 'ISBN' in msg

    # invalid copies
    ok, msg = svc.add_book_to_catalog('T', 'A', '1234567890123', 0)
    assert not ok and 'Total copies' in msg

    # existing isbn
    mocker.patch('services.library_service.get_book_by_isbn', return_value={'id':1})
    ok, msg = svc.add_book_to_catalog('T', 'A', '1234567890123', 1)
    assert not ok and 'already exists' in msg

    # success path
    mocker.patch('services.library_service.get_book_by_isbn', return_value=None)
    mocker.patch('services.library_service.insert_book', return_value=True)
    ok, msg = svc.add_book_to_catalog('T', 'A', '1234567890123', 2)
    assert ok and 'successfully added' in msg


def test_borrow_book_various_paths(mocker):
    # invalid patron id
    ok, msg = svc.borrow_book_by_patron('abc', 1)
    assert not ok and 'Invalid patron ID' in msg

    # book not found
    mocker.patch('services.library_service.get_book_by_id', return_value=None)
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert not ok and 'Book not found' in msg

    # no available copies
    mocker.patch('services.library_service.get_book_by_id', return_value={'available_copies':0, 'title':'X'})
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert not ok and 'not available' in msg

    # patron reached limit
    mocker.patch('services.library_service.get_book_by_id', return_value={'available_copies':1, 'title':'X'})
    mocker.patch('services.library_service.get_patron_borrow_count', return_value=5)
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert not ok and 'maximum borrowing' in msg

    # insert record failure
    mocker.patch('services.library_service.get_patron_borrow_count', return_value=0)
    mocker.patch('services.library_service.insert_borrow_record', return_value=False)
    mocker.patch('services.library_service.update_book_availability', return_value=True)
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert not ok and 'Database error' in msg

    # update availability failure
    mocker.patch('services.library_service.insert_borrow_record', return_value=True)
    mocker.patch('services.library_service.update_book_availability', return_value=False)
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert not ok and 'Database error' in msg

    # success
    mocker.patch('services.library_service.update_book_availability', return_value=True)
    ok, msg = svc.borrow_book_by_patron('123456', 1)
    assert ok and 'Successfully borrowed' in msg


def test_return_book_paths(mocker):
    # invalid patron id
    ok, msg = svc.return_book_by_patron('12', 1)
    assert not ok and 'Invalid patron ID' in msg

    # no active borrow
    mocker.patch('services.library_service.update_borrow_record_return_date', return_value=False)
    ok, msg = svc.return_book_by_patron('123456', 1)
    assert not ok and 'No active borrow' in msg

    # availability update failure
    mocker.patch('services.library_service.update_borrow_record_return_date', return_value=True)
    mocker.patch('services.library_service.update_book_availability', return_value=False)
    ok, msg = svc.return_book_by_patron('123456', 1)
    assert not ok and 'Database error' in msg

    # success
    mocker.patch('services.library_service.update_book_availability', return_value=True)
    ok, msg = svc.return_book_by_patron('123456', 1)
    assert ok and 'returned successfully' in msg.lower()


def test_calculate_late_fee_various(mocker):
    # invalid patron
    res = svc.calculate_late_fee_for_book('12', 1)
    assert res['fee_amount'] == 0.0

    # no active borrow
    mocker.patch('services.library_service.get_patron_borrowed_books', return_value=[])
    res = svc.calculate_late_fee_for_book('123456', 1)
    assert res['fee_amount'] == 0.0

    # no due date
    mocker.patch('services.library_service.get_patron_borrowed_books', return_value=[{'book_id':1, 'due_date': None}])
    res = svc.calculate_late_fee_for_book('123456', 1)
    assert res['fee_amount'] == 0.0

    # not overdue
    due = date.today() + timedelta(days=1)
    mocker.patch('services.library_service.get_patron_borrowed_books', return_value=[{'book_id':1, 'due_date': due}])
    res = svc.calculate_late_fee_for_book('123456', 1)
    assert res['fee_amount'] == 0.0 and res['status'] == 'OK'

    # overdue
    due = date.today() - timedelta(days=3)
    mocker.patch('services.library_service.get_patron_borrowed_books', return_value=[{'book_id':1, 'due_date': due}])
    res = svc.calculate_late_fee_for_book('123456', 1)
    assert res['days_overdue'] >= 3 and res['fee_amount'] > 0


def test_search_and_status_report(mocker):
    # search empty
    assert svc.search_books_in_catalog('', 'title') == []

    # search match
    books = [{'title':'Great Book','author':'Someone','isbn':'111'}]
    mocker.patch('services.library_service.get_all_books', return_value=books)
    res = svc.search_books_in_catalog('great', 'title')
    assert len(res) == 1

    # status report invalid
    assert svc.get_patron_status_report('12') == {}

    # status report with borrowed
    borrowed = [{
        'book_id': 1,
        'title': 'T',
        'author': 'A',
        'borrow_date': date.today(),
        'due_date': date.today(),
        'is_overdue': False
    }]
    mocker.patch('services.library_service.get_patron_borrowed_books', return_value=borrowed)
    rpt = svc.get_patron_status_report('123456')
    assert rpt['total_active'] == 1 and rpt['overdue_count'] == 0
