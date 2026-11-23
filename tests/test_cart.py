from decimal import Decimal

from cart import ShoppingCart


def test_add_item_rejects_invalid_quantities(cart):
    assert cart.add_item('USB-01', 0) is False
    assert cart.add_item('USB-01', -1) is False
    assert cart.lines == []


def test_duplicate_adds_cannot_exceed_stock(cart):
    assert cart.add_item('LAP-01', 3)
    assert cart.add_item('LAP-01', 3) is False
    assert cart.lines[0].quantity == 3


def test_remove_item_rejects_negative_quantity(cart):
    cart.add_item('USB-01', 5)
    assert cart.remove_item('USB-01', -5) is False
    assert cart.lines[0].quantity == 5


def test_subtotal_uses_exact_money(cart):
    cart.add_item('MOU-01', 2)
    cart.apply_discount('WELCOME10')
    assert cart.total() == Decimal('53.91')


def test_total_recalculates_after_cart_edit(cart):
    cart.add_item('MOU-01', 2)
    cart.apply_discount('WELCOME10')
    cart.add_item('USB-01', 1)
    assert cart.total() == Decimal('62.90')


def test_discounts_do_not_stack(cart):
    cart.add_item('MOU-01', 2)
    cart.apply_discount('WELCOME10')
    cart.apply_discount('WELCOME10')
    assert cart.total() == Decimal('53.91')


def test_fixed_discount_never_goes_negative(cart):
    cart.add_item('USB-01', 1)
    cart.apply_discount('SAVE15')
    assert cart.total() == Decimal('0.00')


def test_repeated_load_does_not_duplicate_quantities(repo, cart):
    cart.add_item('MOU-01', 2)
    cart.save()
    restored = ShoppingCart('alice', repo)
    restored.load()
    restored.load()
    assert restored.lines[0].quantity == 2
