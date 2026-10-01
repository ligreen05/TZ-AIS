from sqlalchemy import func

from extensions import db
from models import Category, Product, Stock, Warehouse


def stock_report(warehouse_id=None, category_id=None):
    """Остатки одним запросом (JOIN + GROUP BY)."""
    q = (db.session.query(
            Product.sku, Product.name.label("product_name"),
            Warehouse.name.label("warehouse_name"),
            Category.name.label("category_name"),
            func.coalesce(func.sum(Stock.quantity), 0).label("qty"),
         )
         .join(Stock, Stock.product_id == Product.id)
         .join(Warehouse, Warehouse.id == Stock.warehouse_id)
         .outerjoin(Category, Category.id == Product.category_id)
         .group_by(Product.id, Warehouse.id))
    if warehouse_id:
        q = q.filter(Warehouse.id == warehouse_id)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    return q.order_by(Product.name).all()