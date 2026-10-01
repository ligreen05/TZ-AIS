"""
Общие фикстуры для тестов.

Ключевые принципы:
- Тестовая БД в памяти SQLite (быстро, изолированно).
- Каждый тест получает чистую БД (drop_all/create_all).
- Есть готовые пользователи всех ролей.
- Аутентификация через client.post("/login").
"""
import pytest
from decimal import Decimal

from app import create_app
from config import Config
from extensions import db as _db
from models import (
    Role, User, Category, Unit, Warehouse, StorageLocation,
    Supplier, Customer, Product, Stock,
)


class TestConfig(Config):
    """Отдельная конфигурация для тестов."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False   # выключим CSRF, чтобы не возиться с токенами
    SECRET_KEY = "test-secret"
    PASSWORD_HASH_METHOD = "pbkdf2:sha256:1000"   # быстрее для тестов


@pytest.fixture(scope="session")
def app():
    """Одно приложение на всю сессию тестов."""
    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def db(app):
    """Чистая БД на каждый тест."""
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """HTTP-клиент Flask."""
    return app.test_client()


# ---------- Базовые данные ----------

@pytest.fixture
def roles(db):
    """Создаёт 5 ролей и возвращает dict {code: Role}."""
    roles = {
        "admin": Role(code="admin", name="Администратор"),
        "storekeeper": Role(code="storekeeper", name="Кладовщик"),
        "operator": Role(code="operator", name="Оператор склада"),
        "manager": Role(code="manager", name="Менеджер по продажам"),
        "head": Role(code="head", name="Руководитель склада"),
    }
    db.session.add_all(roles.values())
    db.session.commit()
    return roles


@pytest.fixture
def users(db, roles):
    """Создаёт по одному пользователю каждой роли."""
    users = {}
    for code, role in roles.items():
        u = User(
            username=f"user_{code}",
            full_name=f"Тестовый {code}",
            email=f"{code}@test.local",
            role=role,
        )
        u.set_password("password123")
        db.session.add(u)
        users[code] = u
    db.session.commit()
    return users


@pytest.fixture
def admin_user(users):
    return users["admin"]


@pytest.fixture
def storekeeper_user(users):
    return users["storekeeper"]


# ---------- Справочники ----------

@pytest.fixture
def catalog(db):
    """Категории, единицы, склады, места хранения, контрагенты."""
    cat = Category(name="Тестовая категория")
    unit = Unit(name="шт")
    wh = Warehouse(name="Тестовый склад")
    db.session.add_all([cat, unit, wh])
    db.session.flush()

    loc = StorageLocation(code="A-01", warehouse=wh)
    sup = Supplier(name="ООО «Тестовый поставщик»")
    cus = Customer(name="ООО «Тестовый покупатель»")
    db.session.add_all([loc, sup, cus])
    db.session.commit()

    return {
        "category": cat, "unit": unit, "warehouse": wh,
        "location": loc, "supplier": sup, "customer": cus,
    }


@pytest.fixture
def product(db, catalog):
    """Один тестовый товар."""
    p = Product(
        sku="TEST-001", name="Тестовый товар",
        category=catalog["category"], unit=catalog["unit"],
        min_stock=10,
    )
    db.session.add(p)
    db.session.commit()
    return p


@pytest.fixture
def stock(db, product, catalog):
    """Начальный остаток 100 шт."""
    s = Stock(
        product=product,
        warehouse=catalog["warehouse"],
        location=catalog["location"],
        quantity=Decimal("100"),
        reserved=Decimal("0"),
    )
    db.session.add(s)
    db.session.commit()
    return s


# ---------- Аутентификация ----------

def login(client, username, password="password123"):
    """Логинит пользователя через POST /login."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


@pytest.fixture
def admin_client(client, admin_user):
    login(client, admin_user.username)
    return client


@pytest.fixture
def storekeeper_client(client, storekeeper_user):
    login(client, storekeeper_user.username)
    return client


@pytest.fixture
def anonymous_client(client):
    return client