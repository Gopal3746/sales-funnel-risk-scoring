from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb

from sales_funnel.config import ACCOUNTS_CSV, DB_PATH, PIPELINE_CSV, PRODUCTS_CSV, TEAMS_CSV


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    sources = {
        "raw_sales_pipeline": PIPELINE_CSV,
        "raw_accounts": ACCOUNTS_CSV,
        "raw_products": PRODUCTS_CSV,
        "raw_sales_teams": TEAMS_CSV,
    }
    for table, path in sources.items():
        con.execute(
            f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto('{sql_path(path)}', header=true);"
        )

    for sql_file in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(sql_file.read_text())
        print(f"executed {sql_file.name}")

    total = con.execute("SELECT COUNT(*) FROM mart_opportunities").fetchone()[0]
    print(f"warehouse ready: {DB_PATH} ({total:,} opportunities)")
    con.close()


if __name__ == "__main__":
    main()
