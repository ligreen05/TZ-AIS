from datetime import date, datetime, timezone
from decimal import Decimal

from extensions import db
from models import (
    InventoryDoc,
    InventoryItem,
    ReceiptDoc,
    ReceiptItem,
    ShipmentDoc,
    ShipmentItem,
    Stock,
    TransferDoc,
    TransferItem,
    WriteOffDoc,
    WriteOffItem,
)
from services.stock import apply_stock
from utils.logging import log_action
from utils.transaction import transaction


def _gen_number(prefix: str, model) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    n = db.session.query(db.func.count()).select_from(model).scalar() or 0
    return f"{prefix}-{today}-{n + 1:04d}"


def _parse_items(form, qty_field="quantity"):
    """Возвращает список словарей позиций из формы."""
    pids = form.getlist("product_id[]")
    locs = form.getlist("location_id[]")
    qtys = form.getlist(qty_field if qty_field.endswith("[]") else qty_field + "[]")
    prices = form.getlist("price[]")
    items = []
    for i, pid in enumerate(pids):
        if not pid:
            continue
        qty = qtys[i] if i < len(qtys) else None
        if not qty:
            continue
        items.append({
            "product_id": int(pid),
            "location_id": int(locs[i]) if i < len(locs) and locs[i] else None,
            "quantity": Decimal(qty),
            "price": Decimal(prices[i]) if i < len(prices) and prices[i] else Decimal(0),
        })
    return items


# ---------- Приёмка ----------
def create_receipt(form, user_id: int) -> ReceiptDoc:
    with transaction():
        doc = ReceiptDoc(
            number=_gen_number("ПР", ReceiptDoc),
            doc_date=date.fromisoformat(form["doc_date"]),
            supplier_id=int(form["supplier_id"]),
            warehouse_id=int(form["warehouse_id"]),
            comment=form.get("comment", "").strip(),
            created_by=user_id,
        )
        db.session.add(doc)
        db.session.flush()

        for it in _parse_items(form):
            db.session.add(ReceiptItem(
                doc_id=doc.id, product_id=it["product_id"],
                location_id=it["location_id"],
                quantity=it["quantity"], price=it["price"],
            ))
            apply_stock(it["product_id"], doc.warehouse_id,
                        it["location_id"], it["quantity"])

        log_action("create_receipt", "ReceiptDoc", doc.id, doc.number)
        return doc


# ---------- Отгрузка ----------
def create_shipment(form, user_id: int) -> ShipmentDoc:
    with transaction():
        doc = ShipmentDoc(
            number=_gen_number("РГ", ShipmentDoc),
            doc_date=date.fromisoformat(form["doc_date"]),
            customer_id=int(form["customer_id"]),
            warehouse_id=int(form["warehouse_id"]),
            comment=form.get("comment", "").strip(),
            created_by=user_id,
        )
        db.session.add(doc)
        db.session.flush()

        for it in _parse_items(form):
            db.session.add(ShipmentItem(
                doc_id=doc.id, product_id=it["product_id"],
                location_id=it["location_id"],
                quantity=it["quantity"], price=it["price"],
            ))
            apply_stock(it["product_id"], doc.warehouse_id,
                        it["location_id"], -it["quantity"])

        log_action("create_shipment", "ShipmentDoc", doc.id, doc.number)
        return doc


# ---------- Перемещение ----------
def create_transfer(form, user_id: int) -> TransferDoc:
    with transaction():
        doc = TransferDoc(
            number=_gen_number("ПМ", TransferDoc),
            doc_date=date.fromisoformat(form["doc_date"]),
            warehouse_id=int(form["warehouse_id"]),
            comment=form.get("comment", "").strip(),
            created_by=user_id,
        )
        db.session.add(doc)
        db.session.flush()

        pids = form.getlist("product_id[]")
        froms = form.getlist("from_location_id[]")
        tos = form.getlist("to_location_id[]")
        qtys = form.getlist("quantity[]")

        for pid, f, t, qty in zip(pids, froms, tos, qtys):
            if not pid or not qty or not f or not t:
                continue
            qty_d = Decimal(qty)
            db.session.add(TransferItem(
                doc_id=doc.id, product_id=int(pid),
                from_location_id=int(f), to_location_id=int(t),
                quantity=qty_d,
            ))
            apply_stock(int(pid), doc.warehouse_id, int(f), -qty_d)
            apply_stock(int(pid), doc.warehouse_id, int(t), qty_d)

        log_action("create_transfer", "TransferDoc", doc.id, doc.number)
        return doc


# ---------- Списание ----------
def create_writeoff(form, user_id: int) -> WriteOffDoc:
    with transaction():
        doc = WriteOffDoc(
            number=_gen_number("СП", WriteOffDoc),
            doc_date=date.fromisoformat(form["doc_date"]),
            warehouse_id=int(form["warehouse_id"]),
            reason=form.get("reason", "").strip(),
            comment=form.get("comment", "").strip(),
            created_by=user_id,
        )
        db.session.add(doc)
        db.session.flush()

        for it in _parse_items(form):
            db.session.add(WriteOffItem(
                doc_id=doc.id, product_id=it["product_id"],
                location_id=it["location_id"], quantity=it["quantity"],
            ))
            apply_stock(it["product_id"], doc.warehouse_id,
                        it["location_id"], -it["quantity"])

        log_action("create_writeoff", "WriteOffDoc", doc.id, doc.number)
        return doc


# ---------- Инвентаризация ----------
def create_inventory(form, user_id: int) -> InventoryDoc:
    with transaction():
        warehouse_id = int(form["warehouse_id"])
        doc = InventoryDoc(
            number=f"ИНВ-{date.today().strftime('%Y%m%d')}-"
                   f"{InventoryDoc.query.count() + 1:04d}",
            doc_date=date.fromisoformat(form["doc_date"]),
            warehouse_id=warehouse_id,
            comment=form.get("comment", "").strip(),
            created_by=user_id,
            status="draft",
        )
        db.session.add(doc)
        db.session.flush()

        pids = form.getlist("product_id[]")
        locs = form.getlist("location_id[]")
        facts = form.getlist("fact_qty[]")

        for pid, lid, fact in zip(pids, locs, facts):
            if not pid or fact == "":
                continue
            db.session.add(InventoryItem(
                doc_id=doc.id, product_id=int(pid),
                location_id=int(lid) if lid else None,
                fact_qty=Decimal(fact),
            ))

        log_action("create_inventory", "InventoryDoc", doc.id, doc.number)
        return doc


def apply_inventory(doc: InventoryDoc, user_id: int):
    """Применяет инвентаризацию к остаткам."""
    if doc.status == "done":
        raise ValueError("Инвентаризация уже проведена")

    with transaction():
        stock_index = {
            (s.product_id, s.location_id): s
            for s in Stock.query.filter_by(warehouse_id=doc.warehouse_id).all()
        }
        for item in doc.items:
            key = (item.product_id, item.location_id)
            stock = stock_index.get(key)
            if stock is None:
                stock = Stock(
                    product_id=item.product_id,
                    warehouse_id=doc.warehouse_id,
                    location_id=item.location_id,
                    quantity=Decimal(0), reserved=Decimal(0),
                )
                db.session.add(stock)
                stock_index[key] = stock
            stock.quantity = item.fact_qty

        doc.status = "done"
        log_action("apply_inventory", "InventoryDoc", doc.id, doc.number)



# =========================================================
#  ОТМЕНА ДОКУМЕНТОВ
# =========================================================

def cancel_receipt(doc: ReceiptDoc, user_id: int):
    """Отмена приёмки: уменьшаем остатки."""
    if doc.is_cancelled:
        raise ValueError("Документ уже отменён")
    with transaction():
        for item in doc.items:
            apply_stock(item.product_id, doc.warehouse_id,
                        item.location_id, -item.quantity)
        _mark_cancelled(doc, user_id, "cancel_receipt")


def cancel_shipment(doc: ShipmentDoc, user_id: int):
    """Отмена отгрузки: возвращаем остатки."""
    if doc.is_cancelled:
        raise ValueError("Документ уже отменён")
    with transaction():
        for item in doc.items:
            apply_stock(item.product_id, doc.warehouse_id,
                        item.location_id, item.quantity)
        _mark_cancelled(doc, user_id, "cancel_shipment")


def cancel_transfer(doc: TransferDoc, user_id: int):
    """Отмена перемещения: возвращаем товар обратно."""
    if doc.is_cancelled:
        raise ValueError("Документ уже отменён")
    with transaction():
        for item in doc.items:
            apply_stock(item.product_id, doc.warehouse_id,
                        item.to_location_id, -item.quantity)
            apply_stock(item.product_id, doc.warehouse_id,
                        item.from_location_id, item.quantity)
        _mark_cancelled(doc, user_id, "cancel_transfer")


def cancel_writeoff(doc: WriteOffDoc, user_id: int):
    """Отмена списания: возвращаем остатки."""
    if doc.is_cancelled:
        raise ValueError("Документ уже отменён")
    with transaction():
        for item in doc.items:
            apply_stock(item.product_id, doc.warehouse_id,
                        item.location_id, item.quantity)
        _mark_cancelled(doc, user_id, "cancel_writeoff")


def _mark_cancelled(doc, user_id: int, action_name: str):
    """Общая функция пометки документа отменённым."""
    doc.is_cancelled = True
    doc.cancelled_at = datetime.now(timezone.utc)
    doc.cancelled_by = user_id
    log_action(action_name, doc.__class__.__name__, doc.id, doc.number)