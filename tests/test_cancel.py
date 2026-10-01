"""Тесты отмены документов и смены пароля."""
from decimal import Decimal
from models import ReceiptDoc, Stock
from extensions import db as _db
from tests.conftest import login


def test_change_password_success(admin_client, admin_user, db):
    """Успешная смена пароля."""
    r = admin_client.post("/change-password", data={
        "old_password": "password123",
        "new_password": "newpassword456",
        "confirm_password": "newpassword456",
    }, follow_redirects=True)

    assert r.status_code == 200
    assert "Пароль успешно изменён".encode("utf-8") in r.data

    # Проверяем, что новый пароль работает
    u = _db.session.get(type(admin_user), admin_user.id)
    assert u.check_password("newpassword456")


def test_change_password_wrong_old(admin_client, admin_user):
    """Неверный текущий пароль — отказ."""
    r = admin_client.post("/change-password", data={
        "old_password": "wrong",
        "new_password": "newpassword456",
        "confirm_password": "newpassword456",
    }, follow_redirects=True)

    assert "Неверный текущий пароль".encode("utf-8") in r.data


def test_change_password_mismatch(admin_client):
    """Пароли не совпадают — ошибка валидации."""
    r = admin_client.post("/change-password", data={
        "old_password": "password123",
        "new_password": "newpassword456",
        "confirm_password": "different789",
    }, follow_redirects=True)

    assert "не совпадают".encode("utf-8") in r.data


def test_cancel_receipt_restores_stock(storekeeper_client, product, catalog, stock, db):
    """Отмена приёмки уменьшает остаток обратно."""
    # Сначала приёмка +50
    storekeeper_client.post("/operations/receipts/new", data={
        "doc_date": "2026-10-01",
        "supplier_id": catalog["supplier"].id,
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["50"],
        "price[]": ["100"],
    }, follow_redirects=True)

    s_before = _db.session.get(Stock, stock.id)
    assert float(s_before.quantity) == 150.0

    # Отменяем
    doc = ReceiptDoc.query.first()
    r = storekeeper_client.post(f"/operations/receipts/{doc.id}/cancel",
                                follow_redirects=True)

    assert r.status_code == 200
    s_after = _db.session.get(Stock, stock.id)
    assert float(s_after.quantity) == 100.0
    assert doc.is_cancelled is True


def test_cannot_cancel_twice(storekeeper_client, product, catalog, stock, db):
    """Повторная отмена — предупреждение."""
    storekeeper_client.post("/operations/receipts/new", data={
        "doc_date": "2026-10-01",
        "supplier_id": catalog["supplier"].id,
        "warehouse_id": catalog["warehouse"].id,
        "product_id[]": [str(product.id)],
        "location_id[]": [str(catalog["location"].id)],
        "quantity[]": ["10"],
        "price[]": ["100"],
    }, follow_redirects=True)

    doc = ReceiptDoc.query.first()
    storekeeper_client.post(f"/operations/receipts/{doc.id}/cancel",
                            follow_redirects=True)
    r = storekeeper_client.post(f"/operations/receipts/{doc.id}/cancel",
                                follow_redirects=True)

    assert "уже отменён".encode("utf-8") in r.data


def test_manager_cannot_cancel(client, users, product, catalog, stock):
    """Менеджер не может отменять документы — 403."""
    login(client, users["manager"].username)
    # Создаём документ под storekeeper-ом
    r = client.post("/operations/receipts/1/cancel")
    assert r.status_code == 403
