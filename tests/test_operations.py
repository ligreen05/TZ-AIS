"""Тесты документов и остатков."""
from decimal import Decimal
from models import ReceiptDoc, ShipmentDoc, Stock
from extensions import db as _db


def test_receipt_creates_stock(storekeeper_client, product, catalog, db):
    """Приёмка увеличивает остаток."""
    start = Stock.query.filter_by(
        product_id=product.id,
        warehouse_id=catalog["warehouse"].id,
        location_id=catalog["location"].id,
    ).first()
    start_qty = float(start.quantity) if start else 0.0

    r = storekeeper_client.post("/operations/receipts/new", data={
        "doc_date": "2026-10-01",
        "supplier_id": catalog["supplier"].id,
        "warehouse_id": catalog["warehouse"].id,
        "comment": "Тестовая приёмка",
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["25"],
        "price[]": ["100"],
    }, follow_redirects=True)

    assert r.status_code == 200
    doc = ReceiptDoc.query.first()
    assert doc is not None
    assert doc.items[0].quantity == Decimal("25.000")

    stock = Stock.query.filter_by(
        product_id=product.id,
        warehouse_id=catalog["warehouse"].id,
        location_id=catalog["location"].id,
    ).first()
    assert float(stock.quantity) == start_qty + 25


def test_shipment_decreases_stock(storekeeper_client, product, catalog, stock, db):
    """Отгрузка уменьшает остаток."""
    r = storekeeper_client.post("/operations/shipments/new", data={
        "doc_date": "2026-10-01",
        "customer_id": catalog["customer"].id,
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["30"],
        "price[]": ["150"],
    }, follow_redirects=True)

    assert r.status_code == 200
    s = _db.session.get(Stock, stock.id)
    assert float(s.quantity) == 70.0


def test_shipment_insufficient_stock(storekeeper_client, product, catalog, stock):
    """Отгрузка больше остатка — ошибка, остаток не меняется."""
    r = storekeeper_client.post("/operations/shipments/new", data={
        "doc_date": "2026-10-01",
        "customer_id": catalog["customer"].id,
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["9999"],
        "price[]": ["150"],
    }, follow_redirects=True)

    # Остаток не изменился
    s = _db.session.get(Stock, stock.id)
    assert float(s.quantity) == 100.0
    assert "Недостаточно".encode() in r.data


def test_transfer_moves_stock(storekeeper_client, product, catalog, stock, db):
    """Перемещение: на одном месте минус, на другом плюс."""
    from models import StorageLocation
    loc2 = StorageLocation(code="B-02", warehouse=catalog["warehouse"])
    _db.session.add(loc2)
    _db.session.commit()

    r = storekeeper_client.post("/operations/transfers/new", data={
        "doc_date": "2026-10-01",
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "from_location_id[]": [str(catalog["location"].id)],
        "to_location_id[]": [str(loc2.id)],
        "quantity[]": ["40"],
    }, follow_redirects=True)

    assert r.status_code == 200

    src = Stock.query.filter_by(product_id=product.id,
                                location_id=catalog["location"].id).first()
    dst = Stock.query.filter_by(product_id=product.id,
                                location_id=loc2.id).first()

    assert float(src.quantity) == 60.0
    assert float(dst.quantity) == 40.0


def test_writeoff_decreases_stock(admin_client, product, catalog, stock, db):
    """Списание уменьшает остаток."""
    r = admin_client.post("/operations/writeoffs/new", data={
        "doc_date": "2026-10-01",
        "warehouse_id": catalog["warehouse"].id,
        "reason": "Порча",
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["10"],
    }, follow_redirects=True)

    assert r.status_code == 200
    s = _db.session.get(Stock, stock.id)
    assert float(s.quantity) == 90.0


def test_manager_cannot_create_receipt(client, users, catalog):
    """Менеджер не может создавать приёмку — 403."""
    from tests.conftest import login
    login(client, users["manager"].username)
    r = client.get("/operations/receipts/new")
    assert r.status_code == 403


def test_receipts_list_opens(admin_client):
    r = admin_client.get("/operations/receipts")
    assert r.status_code == 200