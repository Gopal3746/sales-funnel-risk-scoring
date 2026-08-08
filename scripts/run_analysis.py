from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd

from sales_funnel.config import ARTIFACTS_DIR, DB_PATH


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    funnel = con.execute("SELECT * FROM funnel_conversion ORDER BY stage_order").df()
    attrition = con.execute("SELECT * FROM attrition_diagnostics").df()
    cycle = con.execute("SELECT * FROM sales_cycle_summary").df()
    stalled = con.execute("SELECT COUNT(*) AS flagged FROM stalled_deals WHERE stalled").df()

    rows = []
    for _, r in funnel.iterrows():
        rows.append(
            {
                "finding": r["transition"],
                "value": f"{r['conversion_rate']:.1%}",
                "detail": f"{int(r['numerator']):,} of {int(r['denominator']):,} opportunities",
            }
        )
    rows.append(
        {
            "finding": "Observed attrition point",
            "value": attrition.iloc[0]["observed_attrition_point"],
            "detail": f"{int(attrition.iloc[0]['lost_deals']):,} recorded losses",
        }
    )
    rows.append(
        {
            "finding": "Stalled engaging deals",
            "value": f"{int(stalled.iloc[0]['flagged']):,}",
            "detail": "2× product+region P75 duration rule",
        }
    )
    pd.DataFrame(rows).to_csv(ARTIFACTS_DIR / "analysis_summary.csv", index=False)

    print("\nFUNNEL")
    print(funnel.to_string(index=False))
    print("\nATTRITION")
    print(attrition.to_string(index=False))
    print("\nCYCLE")
    print(cycle.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
