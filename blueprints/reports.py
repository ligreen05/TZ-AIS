import csv
import io
from datetime import date, datetime, timedelta

from flask import Blueprint, Response, render_template, request
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from models import (
    Category,
    ReceiptDoc,
    ReceiptItem,
    ShipmentDoc,
    ShipmentItem,
    User,
    Warehouse,
)
from services.reports import stock_report
from utils import require_role

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
@login_required
@require_role("admin", "storekeeper", "head", "manager")
def index():
    return render_template("reports/index.html")


@reports_bp.route("/stock")
@login_required
@require_role("admin", "storekeeper", "head", "manager")
def stock():
    warehouse_id = request.args.get("warehouse", type=int)
    category_id = request.args.get("category", type=int)
    rows = stock_report(warehouse_id, category_id)
    return render_template("reports/stock.html",
        rows=rows,
        warehouses=Warehouse.query.order_by(Warehouse.name).all(),
        categories=Category.query.order_by(Category.name).all(),
        warehouse_id=warehouse_id, category_id=category_id)


@reports_bp.route("/stock.csv")
@login_required
@require_role("admin", "storekeeper", "head", "manager")
def stock_csv():
    warehouse_id = request.args.get("warehouse", type=int)
    rows = stock_report(warehouse_id)

    out = io.StringIO()
    out.write("\ufeff")
    w = csv.writer(out, delimiter=";")
    w.writerow(["Артикул", "Наименование", "Склад", "Категория", "Остаток"])
    for sku, name, wh, cat, qty in rows:
        w.writerow([sku, name, wh, cat or "", f"{float(qty):.3f}"])
    return Response(out.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock.csv"})


@reports_bp.route("/movement")
@login_required
@require_role("admin", "storekeeper", "head", "manager")
def movement():
    date_from = request.args.get("from") or (date.today() - timedelta(days=30)).isoformat()
    date_to = request.args.get("to") or date.today().isoformat()
    d_from = datetime.fromisoformat(date_from).date()
    d_to = datetime.fromisoformat(date_to).date()

    receipts = (db.session.query(ReceiptItem, ReceiptDoc)
                .join(ReceiptDoc, ReceiptDoc.id == ReceiptItem.doc_id)
                .filter(ReceiptDoc.doc_date.between(d_from, d_to)).all())
    shipments = (db.session.query(ShipmentItem, ShipmentDoc)
                 .join(ShipmentDoc, ShipmentDoc.id == ShipmentItem.doc_id)
                 .filter(ShipmentDoc.doc_date.between(d_from, d_to)).all())

    summary = {}
    for item, _ in receipts:
        s = summary.setdefault(item.product_id, {"product": item.product, "in": 0, "out": 0})
        s["in"] += float(item.quantity)
    for item, _ in shipments:
        s = summary.setdefault(item.product_id, {"product": item.product, "in": 0, "out": 0})
        s["out"] += float(item.quantity)

    return render_template("reports/movement.html",
        date_from=date_from, date_to=date_to,
        summary=summary, receipts=receipts, shipments=shipments)


@reports_bp.route("/load")
@login_required
@require_role("admin", "head")
def load():
    rows = (db.session.query(User, func.count(ReceiptDoc.id))
            .outerjoin(ReceiptDoc, ReceiptDoc.created_by == User.id)
            .group_by(User.id).all())
    return render_template("reports/load.html", rows=rows)