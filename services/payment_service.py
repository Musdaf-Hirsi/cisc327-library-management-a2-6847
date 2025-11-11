"""
Simulated Payment Gateway service (treated as external).
Do not modify this file in tests — tests should mock it.
"""
import random


class PaymentGateway:
    """A tiny simulation of an external payment gateway.

    Methods return dicts like {'success': True, 'transaction_id': 'tx123'} or
    {'success': False, 'error': 'declined'}.
    """

    def process_payment(self, amount: float) -> dict:
        # Simulate simple rules: decline amounts > 100, network error chance
        if amount <= 0:
            return {'success': False, 'error': 'invalid_amount'}
        if amount > 100:
            return {'success': False, 'error': 'exceeds_limit'}
        # simulate occasional network hiccup
        if random.random() < 0.02:
            raise RuntimeError('network error')
        return {'success': True, 'transaction_id': f'tx{random.randint(1000,9999)}'}

    def refund_payment(self, transaction_id: str, amount: float) -> dict:
        if not transaction_id:
            return {'success': False, 'error': 'invalid_tx'}
        if amount <= 0:
            return {'success': False, 'error': 'invalid_amount'}
        if amount > 15:
            return {'success': False, 'error': 'exceeds_refund_limit'}
        return {'success': True, 'refund_id': f'rf{random.randint(1000,9999)}'}
