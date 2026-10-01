from functools import wraps

from flask import abort
from flask_login import current_user


def require_role(*roles):
    """Проверяет, что у пользователя есть одна из указанных ролей."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*roles):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator