"""Тесты аутентификации и авторизации."""
from tests.conftest import login


def test_login_page_opens(client):
    """GET /login — страница входа доступна."""
    r = client.get("/login")
    assert r.status_code == 200
    assert "Вход".encode("utf-8") in r.data


def test_login_success(client, admin_user):
    """Успешный вход перенаправляет на дашборд."""
    r = login(client, admin_user.username)
    assert r.status_code == 200
    assert "Панель управления".encode("utf-8") in r.data


def test_login_wrong_password(client, admin_user):
    """Неверный пароль — flash-сообщение, остаёмся на /login."""
    r = login(client, admin_user.username, "wrong")
    assert "Неверный логин или пароль".encode("utf-8") in r.data


def test_login_unknown_user(client):
    """Несуществующий пользователь — та же ошибка."""
    r = login(client, "nobody", "password123")
    assert "Неверный логин или пароль".encode("utf-8") in r.data


def test_logout(client, admin_user):
    """Выход очищает сессию и редиректит на /login."""
    login(client, admin_user.username)
    r = client.get("/logout", follow_redirects=True)
    assert r.status_code == 200
    assert "Вход".encode("utf-8") in r.data


def test_protected_page_requires_login(anonymous_client):
    """Без логина главная недоступна — редирект на /login."""
    r = anonymous_client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_role_admin_only_page(storekeeper_client):
    """Кладовщик не может открыть /admin/users — 403."""
    r = storekeeper_client.get("/admin/users")
    assert r.status_code == 403


def test_role_admin_can_open_admin_page(admin_client):
    """Администратор открывает /admin/users — 200."""
    r = admin_client.get("/admin/users")
    assert r.status_code == 200