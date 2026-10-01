from datetime import date
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import InventoryForm
from models import InventoryDoc, Stock, StorageLocation, Warehouse
from services import apply_inventory, create_inventory
from utils import flash_error, paginate, require_role

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/")
@login_required
@require_role("admin", "storekeeper", "head")
def list_inventories():
    pag = paginate(InventoryDoc.query.order_by(InventoryDoc.created_at.desc()))
    return render_template("inventory/list.html", pagination=pag)


@inventory_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "storekeeper", "head")
def new_inventory():
    form = InventoryForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name)]

    if form.validate_on_submit():
        try:
            doc = create_inventory(request.form, current_user.id)
            flash(f"Инвентаризация {doc.number} создана (черновик)", "success")
            return redirect(url_for("inventory.view", iid=doc.id))
        except Exception as e:
            flash_error(e)

    return render_template("inventory/form.html",
        form=form,
        warehouses=Warehouse.query.order_by(Warehouse.name).all(),
        products=[],
        locations=StorageLocation.query.order_by(StorageLocation.code).all(),
        today=date.today().isoformat(),
    )


@inventory_bp.route("/<int:iid>")
@login_required
@require_role("admin", "storekeeper", "head")
def view(iid):
    doc = db.session.get(InventoryDoc, iid) or abort(404)

    stock_index = {
        (s.product_id, s.location_id): s.quantity
        for s in Stock.query.filter_by(warehouse_id=doc.warehouse_id).all()
    }

    rows = []
    for item in doc.items:
        expected = stock_index.get((item.product_id, item.location_id), Decimal(0))
        rows.append({
            "item": item,
            "expected": expected,
            "diff": item.fact_qty - expected,
        })

    return render_template("inventory/view.html", doc=doc, rows=rows)


@inventory_bp.route("/<int:iid>/apply", methods=["POST"])
@login_required
@require_role("admin", "storekeeper", "head")
def apply(iid):
    doc = db.session.get(InventoryDoc, iid) or abort(404)
    try:
        apply_inventory(doc, current_user.id)
        flash("Инвентаризация проведена, остатки обновлены", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash_error(e)
    return redirect(url_for("inventory.view", iid=iid))