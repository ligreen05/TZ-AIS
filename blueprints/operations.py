from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import ReceiptForm, ShipmentForm, TransferForm, WriteOffForm
from models import (
    Customer,
    Product,
    ReceiptDoc,
    ShipmentDoc,
    StorageLocation,
    Supplier,
    TransferDoc,
    Warehouse,
    WriteOffDoc,
)
from services import (
    create_receipt,
    create_shipment,
    create_transfer,
    create_writeoff,
)
from services.documents import (
    cancel_receipt,
    cancel_shipment,
    cancel_transfer,
    cancel_writeoff,
)
from services.stock import StockError
from utils import flash_error, paginate, require_role

operations_bp = Blueprint("operations", __name__)


def _catalog():
    return dict(
        warehouses=Warehouse.query.order_by(Warehouse.name).all(),
        products=Product.query.filter_by(is_active=True).order_by(Product.name).all(),
        locations=StorageLocation.query.order_by(StorageLocation.code).all(),
        today=date.today().isoformat(),
    )


# =========================================================
#  ПРИЁМКА
# =========================================================

@operations_bp.route("/receipts")
@login_required
@require_role("admin", "operator", "storekeeper", "head")
def receipts():
    pag = paginate(ReceiptDoc.query.order_by(ReceiptDoc.created_at.desc()))
    return render_template("operations/receipts.html", pagination=pag)


@operations_bp.route("/receipts/<int:doc_id>")
@login_required
@require_role("admin", "operator", "storekeeper", "head")
def receipt_view(doc_id):
    doc = db.session.get(ReceiptDoc, doc_id) or abort(404)
    return render_template("operations/view_document.html",
                           doc=doc, doc_type="receipt",
                           title="Приёмка",
                           back_url=url_for("operations.receipts"))


@operations_bp.route("/receipts/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "operator", "storekeeper")
def receipt_new():
    form = ReceiptForm()
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name)]
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name)]

    if form.validate_on_submit():
        try:
            doc = create_receipt(request.form, current_user.id)
            flash(f"Приёмка {doc.number} проведена", "success")
            return redirect(url_for("operations.receipts"))
        except StockError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash_error(e)

    return render_template("operations/receipt_form.html", form=form, **_catalog())


@operations_bp.route("/receipts/<int:doc_id>/cancel", methods=["POST"])
@login_required
@require_role("admin", "storekeeper")
def receipt_cancel(doc_id):
    doc = db.session.get(ReceiptDoc, doc_id) or abort(404)
    try:
        cancel_receipt(doc, current_user.id)
        flash(f"Приёмка {doc.number} отменена", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash_error(e)
    return redirect(url_for("operations.receipt_view", doc_id=doc_id))


# =========================================================
#  ОТГРУЗКА
# =========================================================

@operations_bp.route("/shipments")
@login_required
@require_role("admin", "operator", "storekeeper", "manager", "head")
def shipments():
    pag = paginate(ShipmentDoc.query.order_by(ShipmentDoc.created_at.desc()))
    return render_template("operations/shipments.html", pagination=pag)


@operations_bp.route("/shipments/<int:doc_id>")
@login_required
@require_role("admin", "operator", "storekeeper", "manager", "head")
def shipment_view(doc_id):
    doc = db.session.get(ShipmentDoc, doc_id) or abort(404)
    return render_template("operations/view_document.html",
                           doc=doc, doc_type="shipment",
                           title="Отгрузка",
                           back_url=url_for("operations.shipments"))


@operations_bp.route("/shipments/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "operator", "storekeeper", "manager")
def shipment_new():
    form = ShipmentForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by(Customer.name)]
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name)]

    if form.validate_on_submit():
        try:
            doc = create_shipment(request.form, current_user.id)
            flash(f"Отгрузка {doc.number} проведена", "success")
            return redirect(url_for("operations.shipments"))
        except StockError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash_error(e)

    return render_template("operations/shipment_form.html", form=form, **_catalog())


@operations_bp.route("/shipments/<int:doc_id>/cancel", methods=["POST"])
@login_required
@require_role("admin", "storekeeper")
def shipment_cancel(doc_id):
    doc = db.session.get(ShipmentDoc, doc_id) or abort(404)
    try:
        cancel_shipment(doc, current_user.id)
        flash(f"Отгрузка {doc.number} отменена", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash_error(e)
    return redirect(url_for("operations.shipment_view", doc_id=doc_id))


# =========================================================
#  ПЕРЕМЕЩЕНИЕ
# =========================================================

@operations_bp.route("/transfers")
@login_required
@require_role("admin", "operator", "storekeeper", "head")
def transfers():
    pag = paginate(TransferDoc.query.order_by(TransferDoc.created_at.desc()))
    return render_template("operations/transfers.html", pagination=pag)


@operations_bp.route("/transfers/<int:doc_id>")
@login_required
@require_role("admin", "operator", "storekeeper", "head")
def transfer_view(doc_id):
    doc = db.session.get(TransferDoc, doc_id) or abort(404)
    return render_template("operations/view_document.html",
                           doc=doc, doc_type="transfer",
                           title="Перемещение",
                           back_url=url_for("operations.transfers"))


@operations_bp.route("/transfers/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "operator", "storekeeper")
def transfer_new():
    form = TransferForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name)]

    if form.validate_on_submit():
        try:
            doc = create_transfer(request.form, current_user.id)
            flash(f"Перемещение {doc.number} проведено", "success")
            return redirect(url_for("operations.transfers"))
        except StockError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash_error(e)

    return render_template("operations/transfer_form.html", form=form, **_catalog())


@operations_bp.route("/transfers/<int:doc_id>/cancel", methods=["POST"])
@login_required
@require_role("admin", "storekeeper")
def transfer_cancel(doc_id):
    doc = db.session.get(TransferDoc, doc_id) or abort(404)
    try:
        cancel_transfer(doc, current_user.id)
        flash(f"Перемещение {doc.number} отменено", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash_error(e)
    return redirect(url_for("operations.transfer_view", doc_id=doc_id))


# =========================================================
#  СПИСАНИЕ
# =========================================================

@operations_bp.route("/writeoffs")
@login_required
@require_role("admin", "storekeeper", "head")
def writeoffs():
    pag = paginate(WriteOffDoc.query.order_by(WriteOffDoc.created_at.desc()))
    return render_template("operations/writeoffs.html", pagination=pag)


@operations_bp.route("/writeoffs/<int:doc_id>")
@login_required
@require_role("admin", "storekeeper", "head")
def writeoff_view(doc_id):
    doc = db.session.get(WriteOffDoc, doc_id) or abort(404)
    return render_template("operations/view_document.html",
                           doc=doc, doc_type="writeoff",
                           title="Списание",
                           back_url=url_for("operations.writeoffs"))


@operations_bp.route("/writeoffs/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "storekeeper")
def writeoff_new():
    form = WriteOffForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.order_by(Warehouse.name)]

    if form.validate_on_submit():
        try:
            doc = create_writeoff(request.form, current_user.id)
            flash(f"Списание {doc.number} проведено", "success")
            return redirect(url_for("operations.writeoffs"))
        except StockError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash_error(e)

    return render_template("operations/writeoff_form.html", form=form, **_catalog())


@operations_bp.route("/writeoffs/<int:doc_id>/cancel", methods=["POST"])
@login_required
@require_role("admin", "storekeeper")
def writeoff_cancel(doc_id):
    doc = db.session.get(WriteOffDoc, doc_id) or abort(404)
    try:
        cancel_writeoff(doc, current_user.id)
        flash(f"Списание {doc.number} отменено", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash_error(e)
    return redirect(url_for("operations.writeoff_view", doc_id=doc_id))