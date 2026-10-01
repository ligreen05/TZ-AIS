from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from models import ActionLog, Product, ReceiptDoc, ShipmentDoc, Stock

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    total_products = Product.query.filter_by(is_active=True).count()
    total_stock = db.session.query(func.coalesce(func.sum(Stock.quantity), 0)).scalar()
    total_receipts = ReceiptDoc.query.count()
    total_shipments = ShipmentDoc.query.count()

    low_stock = []
    rows = (db.session.query(
                Product, func.coalesce(func.sum(Stock.quantity), 0).label("qty"))
            .outerjoin(Stock, Stock.product_id == Product.id)
            .group_by(Product.id).all())
    for p, qty in rows:
        if p.min_stock and qty < p.min_stock:
            low_stock.append((p, qty))

    recent_logs = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(10).all()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_stock=total_stock,
        total_receipts=total_receipts,
        total_shipments=total_shipments,
        low_stock=low_stock,
        recent_logs=recent_logs,
    )