from decimal import Decimal

from extensions import db
from models import Stock


class StockError(Exception):
    """Ошибка операции с остатками."""


def apply_stock(product_id: int, warehouse_id: int,
                location_id: int, delta) -> Stock:
    """Изменяет остаток. delta>0 — приход, delta<0 — расход."""
    q = Stock.query.filter_by(
        product_id=product_id,
        warehouse_id=warehouse_id,
        location_id=location_id,
    ).first()

    if q is None:
        q = Stock(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity=Decimal(0),
            reserved=Decimal(0),
        )
        db.session.add(q)
        db.session.flush()

    new_qty = (q.quantity or Decimal(0)) + Decimal(str(delta))
    if new_qty < 0:
        raise StockError(
            f"Недостаточно товара (остаток {q.quantity}, запрошено {abs(delta)})"
        )
    q.quantity = new_qty
    return q