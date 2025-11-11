import pytest
from unittest.mock import Mock

import library_service       # shim at root
from services import payment_service


# ---------- FIXTURE: Gateway Mock ----------
@pytest.fixture
def gateway_mock():
    return Mock(spec=payment_service.PaymentGateway)


# ---------- TESTS FOR pay_late_fees ----------
def test_pay_late_fees_success(mocker, gateway_mock):
    # Stub DB helpers
    mocker.patch('services.library_service.get_book_by_id', return_value={"id": 1, "title": "X"})
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
        'fee_amount': 5.0,
        'days_overdue': 10,
        'status': 'OVERDUE'
    })

    gateway_mock.process_payment.return_value = {'success': True, 'transaction_id': 'tx123'}

    res = library_service.pay_late_fees('123456', 1, gateway_mock)

    assert res['success'] is True
    assert 'transaction_id' in res
    gateway_mock.process_payment.assert_called_once_with(5.0)


def test_pay_late_fees_declined(mocker, gateway_mock):
    mocker.patch('services.library_service.get_book_by_id', return_value={"id": 1})
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
        'fee_amount': 3.5,
        'days_overdue': 7,
        'status': 'OVERDUE'
    })
    gateway_mock.process_payment.return_value = {'success': False, 'error': 'declined'}

    res = library_service.pay_late_fees('123456', 1, gateway_mock)

    assert res['success'] is False
    assert res['message'] == 'Payment declined'
    gateway_mock.process_payment.assert_called_once_with(3.5)


def test_pay_late_fees_invalid_patron_no_gateway_call(mocker, gateway_mock):
    mocker.patch('services.library_service.get_book_by_id', return_value={"id": 1})
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
        'fee_amount': 0.0,
        'days_overdue': 0,
        'status': 'Invalid patron ID'
    })

    res = library_service.pay_late_fees('000000', 1, gateway_mock)

    assert res['success'] is False
    assert 'Invalid patron ID' in res['message']
    gateway_mock.process_payment.assert_not_called()


def test_pay_late_fees_zero_fee_no_gateway_call(mocker, gateway_mock):
    mocker.patch('services.library_service.get_book_by_id', return_value={"id": 1})
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
        'fee_amount': 0.0,
        'days_overdue': 0,
        'status': 'OK'
    })

    res = library_service.pay_late_fees('123456', 1, gateway_mock)

    assert res['success'] is False
    assert 'No fees due' in res['message']
    gateway_mock.process_payment.assert_not_called()


def test_pay_late_fees_gateway_exception(mocker, gateway_mock):
    mocker.patch('services.library_service.get_book_by_id', return_value={"id": 1})
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={
        'fee_amount': 6.0,
        'days_overdue': 12,
        'status': 'OVERDUE'
    })
    gateway_mock.process_payment.side_effect = RuntimeError("network down")

    res = library_service.pay_late_fees('123456', 1, gateway_mock)

    assert res['success'] is False
    assert 'Payment gateway error' in res['message']
    gateway_mock.process_payment.assert_called_once_with(6.0)


# ---------- TESTS FOR refund_late_fee_payment ----------

def test_refund_success(gateway_mock):
    gateway_mock.refund_payment.return_value = {'success': True, 'refund_id': 'rf123'}

    res = library_service.refund_late_fee_payment('tx123', 5.0, gateway_mock)

    assert res['success'] is True
    assert 'refund_id' in res
    gateway_mock.refund_payment.assert_called_once_with('tx123', 5.0)


def test_refund_invalid_transaction_id(gateway_mock):
    res = library_service.refund_late_fee_payment('', 5.0, gateway_mock)

    assert res['success'] is False
    assert 'Invalid transaction ID' in res['message']
    gateway_mock.refund_payment.assert_not_called()


@pytest.mark.parametrize('amt', [-1.0, 0.0, 20.0])
def test_refund_invalid_amount_values(amt, gateway_mock):
    res = library_service.refund_late_fee_payment('tx1', amt, gateway_mock)

    assert res['success'] is False
    gateway_mock.refund_payment.assert_not_called()


def test_refund_non_numeric_amount(gateway_mock):
    res = library_service.refund_late_fee_payment('tx1', 'abc', gateway_mock)

    assert res['success'] is False
    assert res['message'] == 'Invalid amount'
    gateway_mock.refund_payment.assert_not_called()


def test_refund_gateway_exception(gateway_mock):
    gateway_mock.refund_payment.side_effect = RuntimeError("down")

    res = library_service.refund_late_fee_payment('tx1', 5.0, gateway_mock)

    assert res['success'] is False
    assert 'Gateway error' in res['message']
    gateway_mock.refund_payment.assert_called_once_with('tx1', 5.0)


def test_refund_rejected(gateway_mock):
    gateway_mock.refund_payment.return_value = {'success': False, 'error': 'rejected'}

    res = library_service.refund_late_fee_payment('tx1', 5.0, gateway_mock)

    assert res['success'] is False
    assert 'Refund rejected' in res['message']
    gateway_mock.refund_payment.assert_called_once_with('tx1', 5.0)
