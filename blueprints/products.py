from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from extensions import db
from forms import ProductForm
from models import (
    Category,
    Customer,
    Product,
    Stock,
    StorageLocation,
    Supplier,
    Unit,
    Warehouse,
)
from utils import flash_error, log_action, paginate, require_role

products_bp = Blueprint("products", __name__)


def _escape_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@products_bp.route("/")
@login_required
def list_products():
    q = request.args.get("q", "").strip()
    cat_id = request.args.get("category", type=int)

    query = Product.query.filter_by(is_active=True)
    if q:
        safe = _escape_like(q)
        query = query.filter(or_(
            Product.name.ilike(f"%{safe}%", escape="\\"),
            Product.sku.ilike(f"%{safe}%", escape="\\"),
        ))
    if cat_id:
        query = query.filter(Product.category_id == cat_id)

    pagination = paginate(query.order_by(Product.name))

    product_ids = [p.id for p in pagination.items]
    stock_map = {}
    if product_ids:
        rows = (db.session.query(Stock.product_id, func.sum(Stock.quantity))
                .filter(Stock.product_id.in_(product_ids))
                .group_by(Stock.product_id).all())
        stock_map = dict(rows)

    return render_template("products/list.html",
                           pagination=pagination,
                           products=pagination.items,
                           categories=Category.query.order_by(Category.name).all(),
                           q=q, cat_id=cat_id, stock_map=stock_map)

@products_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_role("admin", "operator")
def new_product():
    form = ProductForm()
    form.category_id.choices = [(0, "— не указана —")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name)
    ]
    form.unit_id.choices = [(0, "— не указана —")] + [
        (u.id, u.name) for u in Unit.query.order_by(Unit.name)
    ]

    if form.validate_on_submit():
        try:
            p = Product(
                sku=form.sku.data.strip(),
                name=form.name.data.strip(),
                category_id=form.category_id.data or None,
                unit_id=form.unit_id.data or None,
                min_stock=form.min_stock.data or 0,
            )
            db.session.add(p)
            db.session.flush()
            log_action("create_product", "Product", p.id, f"SKU={p.sku}")
            db.session.commit()
            flash("Товар добавлен", "success")
            return redirect(url_for("products.list_products"))
        except IntegrityError:
            db.session.rollback()
            flash(f"Товар с артикулом {form.sku.data} уже существует", "danger")
        except Exception as e:
            db.session.rollback()
            flash_error(e)

    return render_template("products/form.html", form=form, product=None)


@products_bp.route("/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@require_role("admin", "operator")
def edit_product(pid):
    p = db.session.get(Product, pid) or abort(404)
    form = ProductForm(obj=p)
    form.category_id.choices = [(0, "— не указана —")] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name)
    ]
    form.unit_id.choices = [(0, "— не указана —")] + [
        (u.id, u.name) for u in Unit.query.order_by(Unit.name)
    ]

    if form.validate_on_submit():
        try:
            p.sku = form.sku.data.strip()
            p.name = form.name.data.strip()
            p.category_id = form.category_id.data or None
            p.unit_id = form.unit_id.data or None
            p.min_stock = form.min_stock.data or 0
            log_action("edit_product", "Product", p.id, f"SKU={p.sku}")
            db.session.commit()
            flash("Товар обновлён", "success")
            return redirect(url_for("products.list_products"))
        except IntegrityError:
            db.session.rollback()
            flash(f"Артикул {form.sku.data} уже занят", "danger")
        except Exception as e:
            db.session.rollback()
            flash_error(e)

    return render_template("products/form.html", form=form, product=p)



@products_bp.route("/<int:pid>/delete", methods=["POST"])
@login_required
@require_role("admin")
def delete_product(pid):
    p = db.session.get(Product, pid) or abort(404)
    p.is_active = False
    log_action("deactivate_product", "Product", p.id)
    db.session.commit()
    flash("Товар снят с учёта", "info")
    return redirect(url_for("products.list_products"))


@products_bp.route("/dictionaries")
@login_required
def dictionaries():
    return render_template("products/dictionaries.html",
        categories=Category.query.order_by(Category.name).all(),
        units=Unit.query.order_by(Unit.name).all(),
        suppliers=Supplier.query.order_by(Supplier.name).all(),
        customers=Customer.query.order_by(Customer.name).all(),
        warehouses=Warehouse.query.order_by(Warehouse.name).all(),
        locations=StorageLocation.query.order_by(StorageLocation.code).all(),
    )