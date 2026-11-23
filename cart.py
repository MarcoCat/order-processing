"""Business logic. Several design and correctness issues are intentional."""
from decimal import Decimal

from models import CartLine, to_money

VALID_CODES = ('WELCOME10', 'STUDENT20', 'SAVE15', 'FREESHIP')


def is_valid_quantity(quantity):
    return isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None

    def add_item(self, sku, quantity):
        if not is_valid_quantity(quantity):
            print('Invalid quantity')
            return False
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        requested = quantity + (existing.quantity if existing else 0)
        if product.stock < requested:
            print('Not enough stock')
            return False
        if existing:
            existing.quantity = requested
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity))
        return True

    def remove_item(self, sku, quantity=None):
        if quantity is not None and not is_valid_quantity(quantity):
            print('Invalid quantity')
            return False
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return to_money(sum((line.unit_price * line.quantity for line in self.lines), Decimal('0')))

    def total(self):
        subtotal = self.subtotal()
        if self.discount_code == 'WELCOME10':
            discount = to_money(subtotal * Decimal('0.10'))
        elif self.discount_code == 'STUDENT20':
            discount = to_money(subtotal * Decimal('0.20'))
        elif self.discount_code == 'SAVE15':
            discount = min(Decimal('15.00'), subtotal)
        else:
            discount = Decimal('0.00')
        return subtotal - discount

    def apply_discount(self, code):
        if code not in VALID_CODES:
            print('Invalid coupon')
            return False
        if code == 'FREESHIP':
            print('Shipping is free')
        self.discount_code = code
        return True

    def load(self):
        self.lines = []
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
