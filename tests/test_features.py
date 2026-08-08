import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sales_funnel.features import load_enriched_opportunities, score_stalled_deals


def test_dataset_shape_and_outcomes():
    df = load_enriched_opportunities()
    assert len(df) == 8800
    assert (df["deal_stage"] == "Won").sum() == 4238
    assert (df["deal_stage"] == "Lost").sum() == 2473
    assert (df["deal_stage"] == "Engaging").sum() == 1589
    assert (df["deal_stage"] == "Prospecting").sum() == 500


def test_stalled_deals_are_open_engaging_only():
    df = load_enriched_opportunities()
    stalled = score_stalled_deals(df)
    assert len(stalled) == 1589
    assert stalled["stalled"].sum() == 783
    assert stalled["stall_ratio"].min() >= 0
