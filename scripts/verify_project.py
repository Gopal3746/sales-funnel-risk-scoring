from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from sales_funnel.config import ARTIFACTS_DIR, MODEL_FEATURES, PIPELINE_CSV


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> None:
    raw = pd.read_csv(PIPELINE_CSV)
    check(len(raw) == 8800, "raw opportunity count is 8,800")
    check(raw["opportunity_id"].is_unique, "opportunity IDs are unique")
    check(set(raw["deal_stage"].unique()) == {"Prospecting", "Engaging", "Won", "Lost"}, "stage domain matches source")

    metrics = json.loads((ARTIFACTS_DIR / "metrics.json").read_text())
    check(metrics["wins"] == 4238, "won count is 4,238")
    check(metrics["losses"] == 2473, "lost count is 2,473")
    check(metrics["selected_model"] == "lightgbm", "gradient-boosted model wins CV benchmark")
    check(0.50 <= metrics["cross_validation"]["lightgbm"]["cv_auc_mean"] <= 0.65, "model AUC remains plausible and non-leaky")

    forbidden = {"close_date", "close_value", "deal_stage", "cycle_days", "won"}
    check(not forbidden.intersection(MODEL_FEATURES), "outcome/leakage fields are excluded from predictors")

    scored = pd.read_csv(ARTIFACTS_DIR / "open_deal_scores.csv")
    check(len(scored) == 2089, "all 2,089 open opportunities are scored")
    check(scored["propensity_to_close"].between(0, 1).all(), "propensity scores are bounded")
    check(scored["stalled"].sum() > 0, "stalled-deal heuristic surfaces risk")
    print("\nProject verification complete.")


if __name__ == "__main__":
    main()
