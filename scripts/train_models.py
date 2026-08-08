from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib
import pandas as pd

from sales_funnel.config import ARTIFACTS_DIR, MODEL_FEATURES
from sales_funnel.explanations import explain_rows
from sales_funnel.features import load_enriched_opportunities, score_stalled_deals
from sales_funnel.modeling import save_model_bundle, train_selected_model
from sales_funnel.summaries import deterministic_summary


def main() -> None:
    df = load_enriched_opportunities()
    model, metrics, test_predictions = train_selected_model(df)
    save_model_bundle(model, metrics, test_predictions)

    open_deals = df[df["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    open_deals["propensity_to_close"] = model.predict_proba(open_deals[MODEL_FEATURES])[:, 1]

    stalled = score_stalled_deals(df)[
        [
            "opportunity_id",
            "historical_stage_norm_days",
            "stall_ratio",
            "stalled",
        ]
    ]
    open_deals = open_deals.merge(stalled, on="opportunity_id", how="left")
    open_deals["stalled"] = open_deals["stalled"].fillna(False).astype(bool)
    open_deals["risk_score"] = (
        (1.0 - open_deals["propensity_to_close"]) * 0.65
        + open_deals["stall_ratio"].fillna(0).clip(0, 4) / 4 * 0.35
    )
    open_deals["deal_summary"] = open_deals.apply(lambda r: deterministic_summary(r.to_dict()), axis=1)
    open_deals = open_deals.sort_values(["stalled", "risk_score"], ascending=[False, False])

    cols = [
        "opportunity_id",
        "sales_agent",
        "manager",
        "regional_office",
        "product",
        "account",
        "deal_stage",
        "engage_date",
        "propensity_to_close",
        "days_in_stage",
        "historical_stage_norm_days",
        "stall_ratio",
        "stalled",
        "risk_score",
        "deal_summary",
    ]
    open_deals[cols].to_csv(ARTIFACTS_DIR / "open_deal_scores.csv", index=False)

    # Keep SHAP output compact: explain the 100 highest-risk open deals.
    top = open_deals.head(100).copy()
    shap_df = explain_rows(model, top, top_k=3)
    shap_df.to_csv(ARTIFACTS_DIR / "shap_top_features.csv", index=False)

    metrics["open_deals"] = int(len(open_deals))
    metrics["open_engaging_deals"] = int((open_deals["deal_stage"] == "Engaging").sum())
    metrics["stalled_deals"] = int(open_deals["stalled"].sum())
    metrics["stall_rule"] = "Engaging days >= 2.0 × historical product+region P75 close-cycle duration"
    (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
