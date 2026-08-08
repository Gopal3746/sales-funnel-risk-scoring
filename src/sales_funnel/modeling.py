from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (
    ARTIFACTS_DIR,
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    RANDOM_STATE,
)


def build_preprocessor() -> ColumnTransformer:
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        [
            ("cat", categorical, CATEGORICAL_FEATURES),
            ("num", numeric, NUMERIC_FEATURES),
        ]
    )


def build_models() -> dict[str, Pipeline]:
    logistic = Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "model",
                LogisticRegression(max_iter=2000, C=0.3, random_state=RANDOM_STATE),
            ),
        ]
    )
    boosted = Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "model",
                LGBMClassifier(
                    n_estimators=100,
                    num_leaves=8,
                    learning_rate=0.03,
                    reg_lambda=5.0,
                    verbosity=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    return {"logistic_regression": logistic, "lightgbm": boosted}


def _prepare_closed(df: pd.DataFrame) -> pd.DataFrame:
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["target"] = (closed["deal_stage"] == "Won").astype(int)
    return closed


def cross_validate_models(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    closed = _prepare_closed(df)
    X = closed[MODEL_FEATURES]
    y = closed["target"]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results: dict[str, dict[str, float]] = {}
    for name, model in build_models().items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=1)
        results[name] = {
            "cv_auc_mean": float(scores.mean()),
            "cv_auc_std": float(scores.std()),
        }
    return results


def train_selected_model(df: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame]:
    closed = _prepare_closed(df)
    train, test = train_test_split(
        closed,
        test_size=0.25,
        stratify=closed["target"],
        random_state=RANDOM_STATE,
    )

    models = build_models()
    cv_results = cross_validate_models(df)
    selected_name = max(cv_results, key=lambda k: cv_results[k]["cv_auc_mean"])
    selected = models[selected_name]
    selected.fit(train[MODEL_FEATURES], train["target"])

    probs = selected.predict_proba(test[MODEL_FEATURES])[:, 1]
    preds = (probs >= 0.5).astype(int)
    test_predictions = test[
        ["opportunity_id", "deal_stage", "sales_agent", "product", "account", "close_date"]
    ].copy()
    test_predictions["actual_won"] = test["target"].values
    test_predictions["propensity_to_close"] = probs

    # A temporal holdout is intentionally reported as a stress test, even though
    # the selected model is fit/evaluated with a stratified holdout benchmark.
    temporal_train = closed[closed["close_date"] < "2017-10-01"].copy()
    temporal_test = closed[closed["close_date"] >= "2017-10-01"].copy()
    temporal_model = build_models()[selected_name]
    temporal_model.fit(temporal_train[MODEL_FEATURES], temporal_train["target"])
    temporal_probs = temporal_model.predict_proba(temporal_test[MODEL_FEATURES])[:, 1]

    metrics = {
        "records_total": int(len(df)),
        "records_closed": int(len(closed)),
        "wins": int((closed["target"] == 1).sum()),
        "losses": int((closed["target"] == 0).sum()),
        "closed_win_rate": float(closed["target"].mean()),
        "selected_model": selected_name,
        "holdout_auc": float(roc_auc_score(test["target"], probs)),
        "holdout_average_precision": float(average_precision_score(test["target"], probs)),
        "holdout_accuracy_at_0_5": float(accuracy_score(test["target"], preds)),
        "holdout_brier": float(brier_score_loss(test["target"], probs)),
        "temporal_q4_auc": float(roc_auc_score(temporal_test["target"], temporal_probs)),
        "temporal_train_records": int(len(temporal_train)),
        "temporal_test_records": int(len(temporal_test)),
        "cross_validation": cv_results,
        "feature_policy": "Only fields observable by the engaging stage are used; close_date, close_value, and final deal_stage are excluded from predictors.",
    }
    return selected, metrics, test_predictions


def save_model_bundle(model: Pipeline, metrics: dict, test_predictions: pd.DataFrame) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACTS_DIR / "model.joblib")
    (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    test_predictions.to_csv(ARTIFACTS_DIR / "test_predictions.csv", index=False)

    feature_names = model.named_steps["preprocessor"].get_feature_names_out().tolist()
    (ARTIFACTS_DIR / "feature_names.json").write_text(json.dumps(feature_names, indent=2))
