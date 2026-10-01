"""Тесты CRUD товаров."""
import pytest
from models import Product
from extensions import db as _db


def test_products_list_opens(admin_client):
    r = admin_client.get("/products/")
    assert r.status_code == 200


def test_create_product(admin_client, catalog, db):
    """Админ создаёт товар через форму."""
    r = admin_client.post("/products/new", data={
        "sku": "NEW-001",
        "name": "Новый товар",
        "category_id": catalog["category"].id,
        "unit_id": catalog["unit"].id,
        "min_stock": "5",
    }, follow_redirects=True)

    assert r.status_code == 200
    p = Product.query.filter_by(sku="NEW-001").first()
    assert p is not None
    assert p.name == "Новый товар"


def test_create_product_duplicate_sku(admin_client, product):
    """Дубликат артикула — ошибка."""
    r = admin_client.post("/products/new", data={
        "sku": product.sku,
        "name": "Другой товар",
        "min_stock": "0",
    }, follow_redirects=True)

    # В БД по-прежнему один товар
    assert Product.query.filter_by(sku=product.sku).count() == 1


def test_edit_product(admin_client, product, db):
    """Редактирование меняет поля."""
    r = admin_client.post(f"/products/{product.id}/edit", data={
        "sku": "TEST-001",
        "name": "Изменённое имя",
        "min_stock": "20",
    }, follow_redirects=True)

    assert r.status_code == 200
    updated = _db.session.get(Product, product.id)
    assert updated.name == "Изменённое имя"
    assert float(updated.min_stock) == 20.0


def test_deactivate_product(admin_client, product, db):
    """Удаление = деактивация (is_active=False)."""
    r = admin_client.post(f"/products/{product.id}/delete",
                          follow_redirects=True)
    assert r.status_code == 200
    updated = _db.session.get(Product, product.id)
    assert updated.is_active is False


def test_storekeeper_cannot_create_product(storekeeper_client):
    """Кладовщик не может создавать товары — 403."""
    r = storekeeper_client.get("/products/new")
    assert r.status_code == 403


def test_search_products(admin_client, product):
    """Поиск по артикулу находит товар."""
    r = admin_client.get("/products/?q=TEST-001")
    assert r.status_code == 200
    assert b"TEST-001" in r.data