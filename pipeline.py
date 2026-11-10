"""Lire les CSV Olist, contrôler les données et les charger dans PostgreSQL."""

import argparse
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLUMNS = {
    "customers": ["customer_id", "customer_unique_id", "customer_city", "customer_state"],
    "orders": [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "order_items": ["order_id", "order_item_id", "product_id", "price", "freight_value"],
}


def convert(column, value):
    """Convertir uniquement les champs qui ne sont pas du texte."""
    value = (value or "").strip()
    if not value:
        if column == "order_delivered_customer_date":
            return None
        raise ValueError(f"{column} : valeur manquante")

    if column in ("price", "freight_value"):
        try:
            amount = Decimal(value)
        except InvalidOperation:
            raise ValueError(f"{column} : montant invalide") from None
        if not amount.is_finite() or amount < 0:
            raise ValueError(f"{column} : montant invalide")
        return amount

    if column == "order_item_id":
        item_id = int(value)
        if item_id < 1:
            raise ValueError("order_item_id doit être positif")
        return item_id

    if column.endswith(("_date", "_timestamp")):
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    return value


def read_rows(table, folder):
    """Lire un CSV et vérifier ses colonnes et ses clés."""
    path = folder / f"olist_{table}_dataset.csv"
    columns = COLUMNS[table]
    rows = []
    keys = set()

    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} : colonnes manquantes {sorted(missing)}")

        for line_number, raw in enumerate(reader, start=2):
            try:
                row = tuple(convert(column, raw[column]) for column in columns)
                key = row[:2] if table == "order_items" else row[0]
                if key in keys:
                    raise ValueError(f"clé dupliquée : {key}")
            except ValueError as error:
                raise ValueError(f"{path.name}, ligne {line_number} : {error}") from error

            keys.add(key)
            rows.append(row)

    if not rows:
        raise ValueError(f"{path.name} : fichier vide")
    print(f"{table} : {len(rows):,} lignes validées")
    return rows


def validate_relations(data):
    """Vérifier que les commandes et les articles ont une référence valide."""
    customer_ids = {row[0] for row in data["customers"]}
    order_ids = {row[0] for row in data["orders"]}

    for order in data["orders"]:
        if order[1] not in customer_ids:
            raise ValueError(f"Commande sans client : {order[0]}")

    for item in data["order_items"]:
        if item[0] not in order_ids:
            raise ValueError(f"Article sans commande : {item[0]}")


def load_postgres(data):
    """Remplacer les trois tables dans une seule transaction."""
    import psycopg
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    with psycopg.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
            cursor.execute("TRUNCATE olist.order_items, olist.orders, olist.customers")

            for table, columns in COLUMNS.items():
                column_list = ", ".join(columns)
                with cursor.copy(f"COPY olist.{table} ({column_list}) FROM STDIN") as copy:
                    for row in data[table]:
                        copy.write_row(row)

                cursor.execute(f"SELECT COUNT(*) FROM olist.{table}")
                if cursor.fetchone()[0] != len(data[table]):
                    raise ValueError(f"{table} : nombre de lignes inattendu")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="Vérifier les CSV sans PostgreSQL")
    args = parser.parse_args()

    try:
        data = {}
        for table in COLUMNS:
            data[table] = read_rows(table, ROOT / "data")

        validate_relations(data)
        if args.validate_only:
            print("Validation terminée.")
        else:
            load_postgres(data)
            print("Chargement PostgreSQL terminé.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Erreur : {error}\n")


if __name__ == "__main__":
    main()
