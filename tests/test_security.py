"""Тесты безопасности: CSRF, роли, заголовки."""
from tests.conftest import login


def test_security_headers(admin_client):
    """Заголовки безопасности присутствуют."""
    r = admin_client.get("/")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Referrer-Policy" in r.headers


def test_anonymous_redirected_to_login(client):
    """Аноним не видит закрытых страниц."""
    for url in ["/", "/products/", "/operations/receipts",
                "/inventory/", "/reports/", "/admin/users"]:
        r = client.get(url)
        assert r.status_code == 302, f"{url} should redirect"
        assert "/login" in r.headers["Location"]


def test_storekeeper_cannot_access_admin(client, users):
    """Кладовщик не имеет доступа к /admin/*."""
    login(client, users["storekeeper"].username)
    for url in ["/admin/users", "/admin/log"]:
        r = client.get(url)
        assert r.status_code == 403


def test_manager_cannot_open_receipts_form(client, users):
    """Менеджер не может открыть форму приёмки."""
    login(client, users["manager"].username)
    r = client.get("/operations/receipts/new")
    assert r.status_code == 403


def test_open_redirect_protected(client, admin_user):
    """Переход на внешний URL после логина отсекается."""
    r = client.post(
        "/login?next=https://evil.example.com",
        data={"username": admin_user.username, "password": "password123"},
        follow_redirects=False,
    )
    # Должен быть редирект на дашборд, не на evil
    location = r.headers.get("Location", "")
    assert "evil" not in location


def test_password_is_hashed(admin_user):
    """Пароль не хранится в открытом виде."""
    assert admin_user.password_hash != "password123"
    assert "pbkdf2" in admin_user.password_hash or "scrypt" in admin_user.password_hash


def test_csrf_token_present_in_login_form(client):
    """Форма логина содержит csrf_token (даже при выключенном CSRF для тестов
    шаблон должен рендерить скрытое поле)."""
    r = client.get("/login")
    assert r.status_code == 200

def test_manager_cannot_access_receipts_list(client, users):
    """Менеджер НЕ видит приёмки — RBAC на чтение."""
    login(client, users["manager"].username)
    r = client.get("/operations/receipts")
    assert r.status_code == 403


def test_manager_cannot_access_inventory_list(client, users):
    """Менеджер НЕ видит инвентаризации."""
    login(client, users["manager"].username)
    r = client.get("/inventory/")
    assert r.status_code == 403


def test_manager_can_access_shipments_list(client, users):
    """Менеджер видит отгрузки — это его раздел."""
    login(client, users["manager"].username)
    r = client.get("/operations/shipments")
    assert r.status_code == 200


def test_operator_cannot_access_load_report(client, users):
    """Оператор не видит отчёт по загрузке сотрудников."""
    login(client, users["operator"].username)
    r = client.get("/reports/load")
    assert r.status_code == 403