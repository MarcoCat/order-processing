"""Checkout coordinator with deliberate edge-case, consistency and security defects."""
from decimal import Decimal

from models import OrderResult
from repository import DuplicateRequestError, InsufficientStockError


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if not request_id:
            raise ValueError('request_id is required for checkout')
        previous = self.repository.get_order_by_request_id(request_id)
        if previous:
            return previous
        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', Decimal('0.00'))
        amount = cart.total()
        if amount > 1000:
            if cart.user_id:
                if not request_id:
                    print('Missing request id')
                else:
                    print('Large order')
        lines = list(cart.lines)
        # Stock is decremented before payment and without a shared transaction.
        try:
            order_id = self.repository.reserve_order(cart.user_id, amount, request_id, lines)
        except InsufficientStockError:
            return OrderResult(None, 'out_of_stock', amount)
        except DuplicateRequestError:
            return self.repository.get_order_by_request_id(request_id)
        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response['approved'] else 'declined'
        except Exception:
            status = 'payment_error'
        self.repository.finalize_order(order_id, status, lines, restock=status != 'paid')
        if status == 'paid':
            cart.lines.clear()
            cart.discount_code = None
            cart.save()
        return OrderResult(order_id, status, amount)
