# Defects found and fixed

| # | Where | What could go wrong | Fix |
|---|-------|---------------------|-----|
| 1 | repository.get_product, repository.get_saved_cart | SQL was built with f-strings, so a value like x' OR '1'='1 changed the query (SQL injection). | The queries use ? parameters. |
| 2 | cart.add_item | Quantities of 0, negative numbers, floats or strings were accepted. A negative quantity lowered the total and increased stock at checkout. | Only positive whole numbers are accepted. Anything else returns False. |
| 3 | cart.add_item | Adding a product that was already in the cart only checked the new amount against stock. Adding 3 + 3 laptops with stock 5 gave 6. | The stock check uses the quantity already in the cart plus the new amount. |
| 4 | cart.remove_item | A negative quantity added items to the cart without checking stock (remove_item(sku, -5)). | The quantity is validated the same way as in add_item. |
| 5 | cart.apply_discount, cart.total | The discounted total was stored once and never updated, so items added later were charged at the old total. Applying a code again stacked the discount (WELCOME10 twice gave 19% off). SAVE15 made small orders negative. | Only the discount code is stored. total() recalculates the discount from the current subtotal, so codes can't stack, and SAVE15 is capped at the subtotal. |
| 6 | models, cart | Money used float, which gave totals like 53.910000000000004 that were then charged and stored. | Prices and totals are Decimal, rounded to cents. |
| 7 | checkout.checkout, repository.update_stock | Stock was taken off before payment, one item at a time, with no transaction. A declined or failed payment kept the stock removed. Stock was never re-checked, so it could go negative if another customer bought the item first. | repository.reserve_order takes the stock (only if enough is left) and creates a pending order in one transaction. If anything fails, nothing is saved. finalize_order records the payment result and puts the stock back unless the order was paid. |
| 8 | checkout.checkout | Repeating a checkout with the same request_id (a double click or a retry) charged the customer again. | request_id is required and unique in the database. A repeated request returns the original order without charging again. |
| 9 | checkout.checkout | The cart was emptied and saved even when payment was declined or failed, so the customer lost their cart. | The cart is cleared only when the payment succeeds. |
| 10 | checkout.checkout | The payment token was printed (Charging payment token: ...). | The print was removed. |
| 11 | cart.load | Each call to load() added to the existing lines, so loading twice doubled every quantity. | load() empties the cart before loading. |
| 12 | repository.list_orders | The user_id argument was ignored, so every user's orders were returned. | Filtered with WHERE user_id = ?. |

## Assumptions

- One discount code per cart. Applying a new code replaces the old one.
- FREESHIP doesn't change the total, because the app has no shipping cost.
- SAVE15 takes $15 off and never takes the total below $0.00.
- request_id identifies one checkout attempt. Reusing it returns the original result, even if that was a decline. To retry, the client sends a new request_id.
- Not enough stock at checkout returns status out_of_stock and does not charge.

## Test results

```
$ python -m pytest -q
.................                                                        [100%]
17 passed in 1.42s
```

The tests use a temporary SQLite database (tmp_path) and the supplied FakePaymentGateway, or a gateway that raises an error.
