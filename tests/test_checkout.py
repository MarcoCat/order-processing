from cart import ShoppingCart
from checkout import CheckoutService
from payments import FakePaymentGateway


class ExplodingGateway:
    def charge(self, amount, payment_token):
        raise ConnectionError('gateway unreachable')


def test_declined_payment_restores_stock_and_keeps_cart(repo, cart, stock_of):
    cart.add_item('MOU-01', 2)
    result = CheckoutService(repo, FakePaymentGateway(should_approve=False)).checkout(cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'declined'
    assert stock_of('MOU-01') == 20
    assert len(cart.lines) == 1


def test_payment_error_restores_stock(repo, cart, stock_of):
    cart.add_item('USB-01', 4)
    result = CheckoutService(repo, ExplodingGateway()).checkout(cart, 'TEST_TOKEN', 'req-1')
    assert result.status == 'payment_error'
    assert stock_of('USB-01') == 50


def test_stock_sold_elsewhere_is_not_charged(repo, cart, stock_of):
    cart.add_item('LAP-01', 3)
    other = ShoppingCart('bob', repo)
    other.add_item('LAP-01', 4)
    CheckoutService(repo, FakePaymentGateway()).checkout(other, 'TEST_TOKEN', 'req-bob')
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(cart, 'TEST_TOKEN', 'req-alice')
    assert result.status == 'out_of_stock'
    assert gateway.calls == []
    assert stock_of('LAP-01') == 1


def test_repeated_checkout_with_same_request_id_charges_once(repo, cart, stock_of):
    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    cart.add_item('MOU-01', 1)
    first = service.checkout(cart, 'TEST_TOKEN', 'req-1')
    cart.add_item('MOU-01', 1)
    assert service.checkout(cart, 'TEST_TOKEN', 'req-1') == first
    assert len(gateway.calls) == 1
    assert stock_of('MOU-01') == 19


def test_checkout_does_not_log_payment_token(repo, cart, capsys):
    cart.add_item('MOU-01', 1)
    CheckoutService(repo, FakePaymentGateway()).checkout(cart, 'SECRET_TEST_TOKEN', 'req-1')
    assert 'SECRET_TEST_TOKEN' not in capsys.readouterr().out
