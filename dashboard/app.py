from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

from sales_funnel.config import ARTIFACTS_DIR
from sales_funnel.summaries import claude_summary

st.set_page_config(page_title="Sales Funnel & Deal Scoring", page_icon="📈", layout="wide")


@st.cache_data
def load_artifacts():
    metrics = json.loads((ARTIFACTS_DIR / "metrics.json").read_text())
    scores = pd.read_csv(ARTIFACTS_DIR / "open_deal_scores.csv", parse_dates=["engage_date"])
    shap_df = pd.read_csv(ARTIFACTS_DIR / "shap_top_features.csv")
    raw = pd.read_csv(ROOT / "data" / "raw" / "sales_pipeline.csv")
    return metrics, scores, shap_df, raw


@st.cache_resource
def load_model():
    return joblib.load(ARTIFACTS_DIR / "model.joblib")


metrics, scores, shap_df, raw = load_artifacts()
_ = load_model()

st.title("Sales Funnel & Deal Scoring")
st.caption(
    "DuckDB + SQL funnel analytics, propensity-to-close scoring, stalled-deal detection, SHAP explanations, and optional Claude summaries."
)

with st.sidebar:
    st.header("Filters")
    region_options = sorted(scores["regional_office"].dropna().unique().tolist())
    selected_regions = st.multiselect("Regional office", region_options, default=region_options)
    stage_options = ["Prospecting", "Engaging"]
    selected_stages = st.multiselect("Open stage", stage_options, default=stage_options)
    stalled_only = st.checkbox("Stalled deals only", value=False)
    max_rows = st.slider("Risk table rows", min_value=10, max_value=100, value=25, step=5)

filtered = scores[
    scores["regional_office"].isin(selected_regions) & scores["deal_stage"].isin(selected_stages)
].copy()
if stalled_only:
    filtered = filtered[filtered["stalled"]]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Opportunities", f"{metrics['records_total']:,}")
c2.metric("Closed win rate", f"{metrics['closed_win_rate']:.1%}")
c3.metric("Open pipeline", f"{metrics['open_deals']:,}")
c4.metric("Stalled engaging", f"{metrics['stalled_deals']:,}")

st.subheader("Funnel")
reached_engaging = int((raw["deal_stage"] != "Prospecting").sum())
closed = int(raw["deal_stage"].isin(["Won", "Lost"]).sum())
won = int((raw["deal_stage"] == "Won").sum())
funnel_df = pd.DataFrame(
    {
        "stage": ["All opportunities", "Reached Engaging", "Closed", "Won"],
        "deals": [len(raw), reached_engaging, closed, won],
    }
)
fig = px.funnel(funnel_df, x="deals", y="stage", title="Observed funnel progression")
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "The source contains Prospecting, Engaging, Won, and Lost snapshots rather than a full stage-event log; no intermediate stages are invented."
)

left, right = st.columns([1.1, 0.9])
with left:
    st.subheader("Prioritized open deals")
    table = filtered.sort_values(["stalled", "risk_score"], ascending=[False, False]).head(max_rows).copy()
    show_cols = [
        "opportunity_id",
        "sales_agent",
        "regional_office",
        "product",
        "deal_stage",
        "propensity_to_close",
        "days_in_stage",
        "stall_ratio",
        "stalled",
        "risk_score",
    ]
    st.dataframe(
        table[show_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "propensity_to_close": st.column_config.ProgressColumn(
                "Close propensity", min_value=0.0, max_value=1.0, format="%.1%%"
            ),
            "risk_score": st.column_config.ProgressColumn(
                "Risk score", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "stall_ratio": st.column_config.NumberColumn("Stall ratio", format="%.2fx"),
        },
    )

with right:
    st.subheader("Model benchmark")
    benchmark = pd.DataFrame(
        [
            {
                "model": "Logistic regression",
                "5-fold ROC-AUC": metrics["cross_validation"]["logistic_regression"]["cv_auc_mean"],
            },
            {
                "model": "LightGBM",
                "5-fold ROC-AUC": metrics["cross_validation"]["lightgbm"]["cv_auc_mean"],
            },
        ]
    )
    st.dataframe(benchmark, hide_index=True, use_container_width=True)
    st.metric("Selected holdout ROC-AUC", f"{metrics['holdout_auc']:.3f}")
    st.metric("Q4 temporal stress-test ROC-AUC", f"{metrics['temporal_q4_auc']:.3f}")
    st.info(
        "The model intentionally excludes close value, close date, and final outcome fields. The modest AUC reflects limited predictive signal in this small public CRM dataset."
    )

st.subheader("Deal explanation")
if filtered.empty:
    st.warning("No deals match the selected filters.")
else:
    candidate_ids = filtered.sort_values("risk_score", ascending=False)["opportunity_id"].tolist()
    selected_id = st.selectbox("Opportunity", candidate_ids)
    row = scores.loc[scores["opportunity_id"] == selected_id].iloc[0]

    d1, d2, d3 = st.columns(3)
    d1.metric("Close propensity", f"{row['propensity_to_close']:.1%}")
    d2.metric("Days in Engaging", "—" if pd.isna(row["days_in_stage"]) else f"{int(row['days_in_stage'])}")
    d3.metric("Stall ratio", "—" if pd.isna(row["stall_ratio"]) else f"{row['stall_ratio']:.2f}×")

    deal_shap = shap_df[shap_df["opportunity_id"] == selected_id].sort_values("rank")
    if not deal_shap.empty:
        chart = deal_shap.copy()
        chart["impact"] = chart["shap_value"]
        fig2 = px.bar(
            chart,
            x="impact",
            y="feature",
            orientation="h",
            title="Top SHAP contributions",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("Precomputed SHAP detail is stored for the 100 highest-risk deals.")

    st.markdown("**Rep-facing summary**")
    st.write(row["deal_summary"])
    if st.button("Regenerate with Claude", help="Uses ANTHROPIC_API_KEY when configured; otherwise returns the deterministic fallback."):
        st.write(claude_summary(row.to_dict()))

st.subheader("What the SQL found before modeling")
st.markdown(
    "**Observed attrition concentrates after engagement:** 2,473 opportunities are recorded as Lost, and every closed loss has an engagement date. "
    "Among closed opportunities, 36.8% are losses. Because the source does not log intermediate pipeline events, the analysis stops there rather than assigning losses to fictional stages."
)
