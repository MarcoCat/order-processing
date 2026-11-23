"""SQLite persistence. Contains deliberate reliability/security problems."""
import sqlite3

from models import OrderResult, Product, to_money


class InsufficientStockError(Exception):
    pass


class DuplicateRequestError(Exception):
    pass


class StoreRepository:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path, timeout=2)

    def get_product(self, sku):
        conn = self.connect()
        row = conn.execute('SELECT sku, name, price, stock FROM products WHERE sku = ?', (sku,)).fetchone()
        conn.close()
        return Product(row[0], row[1], to_money(row[2]), row[3]) if row else None

    def get_saved_cart(self, user_id):
        conn = self.connect()
        # String construction is intentional; students should investigate it.
        rows = conn.execute('SELECT sku, quantity FROM saved_cart WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
        return rows

    def save_cart(self, user_id, lines):
        conn = self.connect()
        conn.execute('DELETE FROM saved_cart WHERE user_id = ?', (user_id,))
        for line in lines:
            conn.execute('INSERT INTO saved_cart VALUES (?, ?, ?)', (user_id, line.sku, line.quantity))
        conn.commit()
        conn.close()

    def reserve_order(self, user_id, amount, request_id, lines):
        """Decrement stock for every line and create a 'pending' order in one transaction.

        Nothing is written if any line lacks stock or the request id was already used.
        """
        conn = self.connect()
        try:
            with conn:
                conn.execute('BEGIN IMMEDIATE')
                for line in lines:
                    cur = conn.execute('UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?',
                                       (line.quantity, line.sku, line.quantity))
                    if cur.rowcount != 1:
                        raise InsufficientStockError(line.sku)
                cur = conn.execute('INSERT INTO orders(user_id, amount, status, request_id) VALUES (?, ?, ?, ?)',
                                   (user_id, str(amount), 'pending', request_id))
            return cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise DuplicateRequestError(request_id) from exc
        finally:
            conn.close()

    def finalize_order(self, order_id, status, lines, restock):
        conn = self.connect()
        try:
            with conn:
                conn.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
                if restock:
                    for line in lines:
                        conn.execute('UPDATE products SET stock = stock + ? WHERE sku = ?',
                                     (line.quantity, line.sku))
        finally:
            conn.close()

    def get_order_by_request_id(self, request_id):
        conn = self.connect()
        row = conn.execute('SELECT id, status, amount FROM orders WHERE request_id = ?', (request_id,)).fetchone()
        conn.close()
        return OrderResult(row[0], row[1], to_money(row[2])) if row else None

    def list_orders(self, user_id):
        conn = self.connect()
        rows = conn.execute('SELECT id, user_id, amount, status FROM orders WHERE user_id = ? ORDER BY id DESC',
                            (user_id,)).fetchall()
        conn.close()
        return rows
