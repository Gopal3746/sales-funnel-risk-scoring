from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"
WAREHOUSE_DIR = ROOT / "warehouse"
ARTIFACTS_DIR = ROOT / "artifacts"
DB_PATH = WAREHOUSE_DIR / "sales_funnel.duckdb"

PIPELINE_CSV = DATA_DIR / "sales_pipeline.csv"
ACCOUNTS_CSV = DATA_DIR / "accounts.csv"
PRODUCTS_CSV = DATA_DIR / "products.csv"
TEAMS_CSV = DATA_DIR / "sales_teams.csv"

RANDOM_STATE = 42
SNAPSHOT_DATE = "2017-12-31"

CATEGORICAL_FEATURES = [
    "sales_agent",
    "product",
    "manager",
    "regional_office",
    "series",
    "sector",
    "office_location",
]

NUMERIC_FEATURES = [
    "sales_price",
    "revenue",
    "employees",
    "year_established",
    "account_age",
    "engage_month",
    "engage_dow",
]

MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
