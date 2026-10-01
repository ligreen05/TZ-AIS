"""Тесты админки."""
from models import User, ActionLog


def test_admin_users_page(admin_client):
    r = admin_client.get("/admin/users")
    assert r.status_code == 200


def test_admin_creates_user(admin_client, roles):
    """Админ создаёт пользователя."""
    r = admin_client.post("/admin/users/new", data={
        "username": "newuser",
        "full_name": "Новый Пользователь",
        "email": "new@test.local",
        "password": "password123",
        "role_id": roles["storekeeper"].id,
    }, follow_redirects=True)

    assert r.status_code == 200
    u = User.query.filter_by(username="newuser").first()
    assert u is not None
    assert u.role.code == "storekeeper"


def test_admin_toggle_user(admin_client, storekeeper_user, db):
    """Блокировка пользователя переворачивает флаг."""
    assert storekeeper_user.is_active_flag is True
    admin_client.post(f"/admin/users/{storekeeper_user.id}/toggle",
                      follow_redirects=True)

    u = db.session.get(User, storekeeper_user.id)
    assert u.is_active_flag is False


def test_admin_cannot_block_self(admin_client, admin_user, db):
    """Админ не может заблокировать себя."""
    admin_client.post(f"/admin/users/{admin_user.id}/toggle",
                      follow_redirects=True)
    u = db.session.get(User, admin_user.id)
    assert u.is_active_flag is True


def test_log_page(admin_client):
    r = admin_client.get("/admin/log")
    assert r.status_code == 200


def test_login_writes_log(client, admin_user, db):
    """Успешный вход пишет запись в ActionLog."""
    from tests.conftest import login
    login(client, admin_user.username)
    log = ActionLog.query.filter_by(action="login").first()
    assert log is not None
    assert log.user_id == admin_user.id