"""Contrôles rapides sans PostgreSQL ni dépendance de test."""
import tempfile
from pathlib import Path

from pipeline import convert, read_rows, validate_relations


def check_error(function, *args):
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError("Une erreur de validation était attendue")


def test_invalid_money():
    for value in ("-1", "NaN", "Infinity", "abc", ""):
        check_error(convert, "price", value)


def test_missing_delivery_allowed():
    assert convert("order_delivered_customer_date", "") is None


def test_duplicates_rejected():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "olist_customers_dataset.csv"
        path.write_text(
            "customer_id,customer_unique_id,customer_city,customer_state\na,u,city,SP\na,u,city,SP\n",
            encoding="utf-8",
        )
        check_error(read_rows, "customers", Path(folder))


def test_orphan_rejected():
    data = {"customers": [("c1",)], "orders": [("o1", "missing")], "order_items": []}
    check_error(validate_relations, data)


if __name__ == "__main__":
    test_invalid_money()
    test_missing_delivery_allowed()
    test_duplicates_rejected()
    test_orphan_rejected()
    print("4 tests réussis.")
