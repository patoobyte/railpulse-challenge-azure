import argparse
import csv
import json
import os
from pathlib import Path

import pyodbc


STATIC_DIR = Path("static")
LOCAL_SETTINGS_PATH = Path("local.settings.json")
BATCH_SIZE = 10000

IMPORT_ORDER = [
    ("agency", "agency.txt"),
    ("calendar", "calendar.txt"),
    ("routes", "routes.txt"),
    ("stops", "stops.txt"),
    ("trips", "trips.txt"),
    ("calendar_dates", "calendar_dates.txt"),
    ("stop_times", "stop_times.txt"),
]


def empty_to_none(row):
    clean_row = {}

    for key, value in row.items():
        if value == "":
            clean_row[key] = None
        else:
            clean_row[key] = value

    return clean_row


def get_connection_string():
    connection_string = os.environ.get("SQL_CONNECTION_STRING")

    if not connection_string and LOCAL_SETTINGS_PATH.exists():
        with LOCAL_SETTINGS_PATH.open(encoding="utf-8") as file:
            local_settings = json.load(file)

        connection_string = (
            local_settings
            .get("Values", {})
            .get("SQL_CONNECTION_STRING")
        )

    if not connection_string:
        raise ValueError("Missing SQL_CONNECTION_STRING environment variable.")

    return connection_string


def selected_imports(selected_tables):
    if not selected_tables:
        return IMPORT_ORDER

    known_tables = {table_name for table_name, _ in IMPORT_ORDER}
    unknown_tables = set(selected_tables) - known_tables

    if unknown_tables:
        raise ValueError(f"Unknown table(s): {', '.join(sorted(unknown_tables))}")

    return [
        (table_name, file_name)
        for table_name, file_name in IMPORT_ORDER
        if table_name in selected_tables
    ]


def import_table(connection, table_name, file_name):
    file_path = STATIC_DIR / file_name
    total_rows = 0

    if not file_path.exists():
        raise FileNotFoundError(f"Missing static file: {file_path}")

    with file_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames

        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join([f"[{column}]" for column in columns])

        sql = f"""
        INSERT INTO [{table_name}] ({column_names})
        VALUES ({placeholders})
        """

        rows = []
        cursor = connection.cursor()
        cursor.fast_executemany = True

        for row in reader:
            clean_row = empty_to_none(row)
            values = []

            for column in columns:
                values.append(clean_row[column])

            rows.append(values)

            if len(rows) == BATCH_SIZE:
                cursor.executemany(sql, rows)
                connection.commit()
                total_rows += len(rows)
                print(f"Imported {total_rows} rows into {table_name}")
                rows = []

        if len(rows) > 0:
            cursor.executemany(sql, rows)
            connection.commit()
            total_rows += len(rows)

    print(f"Finished {table_name}: {total_rows} rows imported")


def show_counts(connection, imports):
    print("\nRow counts:")

    cursor = connection.cursor()

    for table_name, _ in imports:
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import GTFS static text files into Azure SQL."
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        help="Optional table names to import, for example: --tables agency routes",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    imports = selected_imports(args.tables)

    connection = pyodbc.connect(get_connection_string())

    try:
        for table_name, file_name in imports:
            import_table(connection, table_name, file_name)

        show_counts(connection, imports)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
