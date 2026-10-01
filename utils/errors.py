"""Утилиты для безопасной обработки исключений."""
from flask import current_app, flash

from utils.logging import get_logger


def flash_error(
    exc: Exception,
    user_message: str = "Не удалось выполнить операцию. Обратитесь к администратору.",
):
    """
    Логирует реальную ошибку, а пользователю показывает безопасное сообщение.
    В DEV-режиме показывает детали — удобно для отладки.
    """
    get_logger().exception(f"Application error: {exc}")

    if current_app.debug:
        flash(f"[DEV] {type(exc).__name__}: {exc}", "danger")
    else:
        flash(user_message, "danger")