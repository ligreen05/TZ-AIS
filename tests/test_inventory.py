"""Тесты инвентаризации."""
from decimal import Decimal
from models import InventoryDoc, Stock
from extensions import db as _db


def test_create_inventory_draft(storekeeper_client, product, catalog, stock):
    """Создаётся черновик инвентаризации."""
    r = storekeeper_client.post("/inventory/new", data={
        "doc_date": "2026-10-01",
        "warehouse_id": catalog["warehouse"].id,
        "comment": "Плановая",
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "fact_qty[]": ["95"],
    }, follow_redirects=True)

    assert r.status_code == 200
    doc = InventoryDoc.query.first()
    assert doc is not None
    assert doc.status == "draft"


def test_apply_inventory_updates_stock(storekeeper_client, product, catalog, stock, db):
    """После применения остаток = факт."""
    storekeeper_client.post("/inventory/new", data={
        "doc_date": "2026-10-01",
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "fact_qty[]": ["80"],
    }, follow_redirects=True)

    doc = InventoryDoc.query.first()
    r = storekeeper_client.post(f"/inventory/{doc.id}/apply",
                                follow_redirects=True)
    assert r.status_code == 200

    s = _db.session.get(Stock, stock.id)
    assert float(s.quantity) == 80.0


def test_cannot_apply_twice(storekeeper_client, product, catalog, stock):
    """Повторное применение — предупреждение."""
    storekeeper_client.post("/inventory/new", data={
        "doc_date": "2026-10-01",
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "fact_qty[]": ["80"],
    }, follow_redirects=True)

    doc = InventoryDoc.query.first()
    storekeeper_client.post(f"/inventory/{doc.id}/apply", follow_redirects=True)
    r = storekeeper_client.post(f"/inventory/{doc.id}/apply",
                                follow_redirects=True)

    assert "уже проведена".encode() in r.data