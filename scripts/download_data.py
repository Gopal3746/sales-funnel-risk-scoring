"""Download the four public CRM CSVs from a GitHub mirror of the Kaggle/Maven dataset."""
from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://raw.githubusercontent.com/rivaldo1403/Maven-Sales-Challenge/refs/heads/main"
FILES = ["sales_pipeline.csv", "accounts.csv", "products.csv", "sales_teams.csv"]

for name in FILES:
    target = OUT / name
    print(f"downloading {name}")
    urlretrieve(f"{BASE}/{name}", target)
print("done")
