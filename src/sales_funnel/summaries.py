from __future__ import annotations

import os
import math


def deterministic_summary(row: dict) -> str:
    def num(value, default=0.0):
        try:
            value = float(value)
            return default if math.isnan(value) else value
        except (TypeError, ValueError):
            return default

    score = num(row.get("propensity_to_close"), 0.0)
    stall_ratio = num(row.get("stall_ratio"), 0.0)
    days = int(num(row.get("days_in_stage"), 0.0))
    norm = int(num(row.get("historical_stage_norm_days"), 0.0))
    product = row.get("product", "this product")
    rep = row.get("sales_agent", "the assigned rep")

    if stall_ratio >= 3:
        severity = "well beyond"
    elif stall_ratio >= 2:
        severity = "above"
    else:
        severity = "near"

    return (
        f"{rep}'s {product} opportunity has a {score:.0%} close propensity and has spent "
        f"{days} days in Engaging, {severity} the {norm}-day historical norm; prioritize a "
        "next-step check before forecast review."
    )


def claude_summary(row: dict) -> str:
    """Generate one concise sales-rep action sentence; gracefully falls back without an API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return deterministic_summary(row)

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        prompt = (
            "Write exactly one sentence for a sales rep. Be factual, concise, and action-oriented. "
            "Do not claim causality. Deal facts: "
            f"opportunity={row.get('opportunity_id')}; rep={row.get('sales_agent')}; "
            f"product={row.get('product')}; account={row.get('account')}; "
            f"close_propensity={float(row.get('propensity_to_close', 0)):.3f}; "
            f"days_in_engaging={int(row.get('days_in_stage', 0) or 0)}; "
            f"historical_norm_days={int(row.get('historical_stage_norm_days', 0) or 0)}; "
            f"stall_ratio={float(row.get('stall_ratio', 0)):.2f}."
        )
        message = client.messages.create(
            model=model,
            max_tokens=90,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:
        return deterministic_summary(row)
