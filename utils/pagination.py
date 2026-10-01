from flask import request

from config import Config


def paginate(query, per_page=None, max_page=10000):
    """
    Единая пагинация. Возвращает объект Pagination.
    Автоматически ограничивает номер страницы.
    """
    per_page = per_page or Config.ITEMS_PER_PAGE
    per_page = min(per_page, Config.MAX_PER_PAGE)

    page = request.args.get("page", 1, type=int)
    if page < 1 or page > max_page:
        page = 1

    return query.paginate(page=page, per_page=per_page, error_out=False)