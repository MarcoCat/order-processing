from decimal import Decimal

from models import CartLine


def test_get_product_is_not_vulnerable_to_sql_injection(repo):
    assert repo.get_product("x' OR '1'='1") is None


def test_list_orders_only_returns_that_users_orders(repo):
    lines = [CartLine('USB-01', 'USB cable', Decimal('9.99'), 1)]
    repo.reserve_order('alice', Decimal('9.99'), 'req-a', lines)
    repo.reserve_order('bob', Decimal('9.99'), 'req-b', lines)
    assert [row[1] for row in repo.list_orders('alice')] == ['alice']
