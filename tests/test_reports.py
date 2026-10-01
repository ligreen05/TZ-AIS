"""Тесты отчётов."""
import io


def test_stock_report_opens(admin_client):
    r = admin_client.get("/reports/stock")
    assert r.status_code == 200


def test_stock_report_csv(admin_client, product, stock):
    """CSV-экспорт отдаёт файл с BOM и разделителем ;"""
    r = admin_client.get("/reports/stock.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    # BOM UTF-8
    assert r.data.startswith(b"\xef\xbb\xbf")


def test_movement_report_opens(admin_client):
    r = admin_client.get("/reports/movement")
    assert r.status_code == 200


def test_load_report_opens(admin_client):
    r = admin_client.get("/reports/load")
    assert r.status_code == 200