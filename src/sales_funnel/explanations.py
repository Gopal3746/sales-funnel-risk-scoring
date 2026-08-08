from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from .config import MODEL_FEATURES


def explain_rows(model_pipeline, rows: pd.DataFrame, top_k: int = 3) -> pd.DataFrame:
    """Return the strongest absolute SHAP contributions for each supplied row."""
    if rows.empty:
        return pd.DataFrame(
            columns=["opportunity_id", "feature", "feature_value", "shap_value", "direction", "rank"]
        )

    pre = model_pipeline.named_steps["preprocessor"]
    model = model_pipeline.named_steps["model"]
    X = pre.transform(rows[MODEL_FEATURES])
    if hasattr(X, "toarray"):
        X = X.toarray()
    feature_names = np.asarray(pre.get_feature_names_out())
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(X)
    if isinstance(values, list):
        values = values[-1]
    values = np.asarray(values)

    records = []
    for i, (_, row) in enumerate(rows.iterrows()):
        order = np.argsort(np.abs(values[i]))[::-1][:top_k]
        for rank, idx in enumerate(order, start=1):
            records.append(
                {
                    "opportunity_id": row["opportunity_id"],
                    "feature": str(feature_names[idx]),
                    "feature_value": None,
                    "shap_value": float(values[i][idx]),
                    "direction": "raises score" if values[i][idx] > 0 else "lowers score",
                    "rank": rank,
                }
            )
    return pd.DataFrame(records)
