from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ACCOUNTS_CSV, PIPELINE_CSV, PRODUCTS_CSV, TEAMS_CSV, SNAPSHOT_DATE


def load_enriched_opportunities() -> pd.DataFrame:
    pipeline = pd.read_csv(PIPELINE_CSV, parse_dates=["engage_date", "close_date"])
    teams = pd.read_csv(TEAMS_CSV)
    products = pd.read_csv(PRODUCTS_CSV)
    accounts = pd.read_csv(ACCOUNTS_CSV)

    # The source pipeline uses "GTXPro" while the product dimension uses "GTX Pro".
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})
    accounts["sector"] = accounts["sector"].replace({"technolgy": "technology"})

    df = (
        pipeline.merge(teams, on="sales_agent", how="left", validate="many_to_one")
        .merge(products, on="product", how="left", validate="many_to_one")
        .merge(accounts, on="account", how="left", validate="many_to_one")
    )

    df["engage_month"] = df["engage_date"].dt.month
    df["engage_dow"] = df["engage_date"].dt.dayofweek
    df["account_age"] = df["engage_date"].dt.year - df["year_established"]
    df["cycle_days"] = (df["close_date"] - df["engage_date"]).dt.days
    df["is_closed"] = df["deal_stage"].isin(["Won", "Lost"])
    df["won"] = np.where(df["is_closed"], (df["deal_stage"] == "Won").astype(int), np.nan)

    snapshot = pd.Timestamp(SNAPSHOT_DATE)
    df["days_in_stage"] = np.where(
        df["deal_stage"].eq("Engaging"),
        (snapshot - df["engage_date"]).dt.days,
        np.nan,
    )
    return df


def build_stall_benchmarks(df: pd.DataFrame, quantile: float = 0.75) -> pd.DataFrame:
    closed = df[df["is_closed"] & df["cycle_days"].notna()].copy()
    grouped = (
        closed.groupby(["product", "regional_office"], dropna=False)["cycle_days"]
        .quantile(quantile)
        .rename("historical_stage_norm_days")
        .reset_index()
    )
    overall = float(closed["cycle_days"].quantile(quantile))
    grouped["historical_stage_norm_days"] = grouped["historical_stage_norm_days"].fillna(overall)
    return grouped


def score_stalled_deals(df: pd.DataFrame, ratio_threshold: float = 2.0) -> pd.DataFrame:
    open_engaging = df[df["deal_stage"].eq("Engaging")].copy()
    benchmarks = build_stall_benchmarks(df)
    open_engaging = open_engaging.merge(
        benchmarks, on=["product", "regional_office"], how="left"
    )
    fallback = float(df.loc[df["is_closed"], "cycle_days"].quantile(0.75))
    open_engaging["historical_stage_norm_days"] = open_engaging[
        "historical_stage_norm_days"
    ].fillna(fallback)
    open_engaging["stall_ratio"] = (
        open_engaging["days_in_stage"] / open_engaging["historical_stage_norm_days"]
    )
    open_engaging["stalled"] = open_engaging["stall_ratio"] >= ratio_threshold
    return open_engaging
