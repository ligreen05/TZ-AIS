import logging
from logging.handlers import RotatingFileHandler

from flask_login import current_user

from config import Config

_logger = None


def get_logger():
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("warehouse")
    logger.setLevel(Config.LOG_LEVEL)

    if not logger.handlers:
        handler = RotatingFileHandler(
            Config.LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    _logger = logger
    return logger


def log_action(action: str, entity: str = None, entity_id: int = None,
               details: str = None):
    """Пишет действие в ActionLog и в файловый лог."""
    from extensions import db
    from models import ActionLog

    uid = current_user.id if current_user and current_user.is_authenticated else None
    entry = ActionLog(
        user_id=uid, action=action, entity=entity,
        entity_id=entity_id, details=details,
    )
    db.session.add(entry)
    get_logger().info(
        f"user={uid} action={action} entity={entity} id={entity_id} details={details}"
    )