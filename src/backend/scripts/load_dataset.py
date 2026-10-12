"""
Loads dataset/raw/cloudwise_billing.csv into the cost_records table.

Usage:
  export DATABASE_URL=postgresql://user:password@localhost:5432/cloudwise
  python src/backend/scripts/load_dataset.py            # append (skips existing rows)
  python src/backend/scripts/load_dataset.py --reset    # wipe cost_records first
"""

import argparse
import csv
import io
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()


CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "dataset", "raw", "cloudwise_billing.csv"
)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")

COLUMNS = [
    "date", "billing_period", "service", "region", "resource_id",
    "usage_hours", "storage_gb", "avg_cpu_utilization", "cost",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="truncate cost_records before loading")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("Set DATABASE_URL first, e.g. postgresql://user:password@localhost:5432/cloudwise")

    conn = psycopg2.connect(database_url)
    try:
        with conn, conn.cursor() as cur:
            # make sure tables exist
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                cur.execute(f.read())

            if args.reset:
                cur.execute("TRUNCATE cost_records RESTART IDENTITY")

            # stage the CSV, then insert with ON CONFLICT so re-runs are safe
            cur.execute("CREATE TEMP TABLE staging (LIKE cost_records INCLUDING DEFAULTS) ON COMMIT DROP")
            cur.execute("ALTER TABLE staging DROP COLUMN id")

            buffer = io.StringIO()
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                writer = csv.writer(buffer)
                for row in reader:
                    writer.writerow([row[c] for c in COLUMNS])
            buffer.seek(0)

            cur.copy_expert(f"COPY staging ({', '.join(COLUMNS)}) FROM STDIN WITH CSV", buffer)
            cur.execute(f"""
                INSERT INTO cost_records ({', '.join(COLUMNS)})
                SELECT {', '.join(COLUMNS)} FROM staging
                ON CONFLICT (date, resource_id) DO NOTHING
            """)
            inserted = cur.rowcount

            cur.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM cost_records")
            total, first, last = cur.fetchone()
            print(f"Inserted {inserted:,} new rows. cost_records now has {total:,} rows ({first} -> {last}).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
