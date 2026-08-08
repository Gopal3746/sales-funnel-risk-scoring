import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sales_funnel.summaries import deterministic_summary


def test_summary_is_one_sentence_and_actionable():
    text = deterministic_summary(
        {
            "sales_agent": "Example Rep",
            "product": "GTX Pro",
            "propensity_to_close": 0.42,
            "days_in_stage": 180,
            "historical_stage_norm_days": 80,
            "stall_ratio": 2.25,
        }
    )
    assert "42%" in text
    assert "180 days" in text
    assert "prioritize" in text.lower()
    assert text.count(".") == 1
