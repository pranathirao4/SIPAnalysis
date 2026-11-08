"""Unit tests for deterministic financial engine (core/compute.py)
and static data (core/static_data.py) against Evidence_Log/golden_set.json.
"""

import json
from pathlib import Path
import pytest

from core.compute import compute_sip, format_inr, format_pct, format_units
from core.static_data import PARAG_PARIKH_DATA, FUND_HISTORY_HORIZONS, FUND_HISTORY_QUIZ


@pytest.fixture
def golden_set_data():
    """Load scenarios from Evidence_Log/golden_set.json."""
    path = Path(__file__).resolve().parent.parent / "Evidence_Log" / "golden_set.json"
    assert path.exists(), f"golden_set.json not found at {path}"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_all_ten_scenarios(golden_set_data):
    """Verify compute_sip reproduces all 10 golden set scenarios within tolerance."""
    scenarios = golden_set_data["scenarios"]
    tolerance = golden_set_data.get("tolerance_rupees", 1)

    assert len(scenarios) == 10, f"Expected 10 scenarios, found {len(scenarios)}"

    for name, sc in scenarios.items():
        monthly = sc["monthly"]
        navs = sc["navs"]
        exp = sc["expected"]
        exp_relation = sc["relation"]

        result = compute_sip(monthly, navs, scenario_name=name)

        # 1. Invested amount
        assert abs(result["invested"] - exp["invested"]) <= tolerance, (
            f"[{name}] Invested mismatch: got {result['invested']}, expected {exp['invested']}"
        )

        # 2. Units accumulated
        assert abs(result["units_total"] - exp["units"]) <= 0.01, (
            f"[{name}] Units mismatch: got {result['units_total']}, expected {exp['units']}"
        )

        # 3. Portfolio current value
        assert abs(result["value"] - exp["value"]) <= tolerance, (
            f"[{name}] Value mismatch: got {result['value']}, expected {exp['value']}"
        )

        # 4. Absolute difference
        assert abs(result["diff"] - exp["diff"]) <= tolerance, (
            f"[{name}] Difference mismatch: got {result['diff']}, expected {exp['diff']}"
        )

        # 5. Personal return percentage
        assert abs(result["return_pct"] - exp["ret"]) <= 0.02, (
            f"[{name}] Return % mismatch: got {result['return_pct']}, expected {exp['ret']}"
        )

        # 6. Average purchase cost
        assert abs(result["avg_cost"] - exp["avg_cost"]) <= 0.02, (
            f"[{name}] Average cost mismatch: got {result['avg_cost']}, expected {exp['avg_cost']}"
        )

        # 7. Fund point-to-point return
        assert abs(result["fund_return_pct"] - exp["fund_ret"]) <= 0.02, (
            f"[{name}] Fund return % mismatch: got {result['fund_return_pct']}, expected {exp['fund_ret']}"
        )

        # 8. Relation flag
        assert result["relation"] == exp_relation, (
            f"[{name}] Relation mismatch: got '{result['relation']}', expected '{exp_relation}'"
        )


def test_base_scenario_exact_values():
    """Verify base scenario exact figures required across all UI screens."""
    monthly = 2000
    navs = [48.50, 52.00, 54.00, 55.00, 53.95, 50.00, 44.75]
    result = compute_sip(monthly, navs, scenario_name="base")

    assert result["invested"] == 14000
    assert result["value"] == 12300
    assert result["diff"] == -1700
    assert result["return_pct"] == -12.14
    assert result["units_total"] == 274.86
    assert result["avg_cost"] == 50.93
    assert result["nav_now"] == 44.75
    assert result["nav_start"] == 48.50
    assert result["fund_return_pct"] == -7.73
    assert result["relation"] == "sip_lower"

    # Formatted strings
    assert result["formatted"]["invested"] == "₹14,000"
    assert result["formatted"]["value"] == "₹12,300"
    assert result["formatted"]["diff"] == "-₹1,700"
    assert result["formatted"]["return_pct"] == "-12.14%"
    assert result["formatted"]["avg_cost"] == "₹50.93"
    assert result["formatted"]["nav_now"] == "₹44.75"
    assert result["formatted"]["units_total"] == "274.86"


def test_home_screen_portfolio_totals():
    """Verify combined portfolio totals for Home screen (Axis base + Parag Parikh)."""
    axis_res = compute_sip(2000, [48.50, 52.00, 54.00, 55.00, 53.95, 50.00, 44.75], "base")

    total_invested = axis_res["invested"] + PARAG_PARIKH_DATA["invested"]
    total_value = axis_res["value"] + PARAG_PARIKH_DATA["value"]
    total_diff = total_value - total_invested
    overall_return_pct = round((total_diff / total_invested) * 100, 2)
    active_sips = 2
    monthly_sip_total = axis_res["monthly"] + PARAG_PARIKH_DATA["monthly_amount"]

    assert total_invested == 35000
    assert total_value == 35400
    assert total_diff == 400
    assert overall_return_pct == 1.14
    assert active_sips == 2
    assert monthly_sip_total == 5000

    # Test formatted display strings
    assert format_inr(total_invested) == "₹35,000"
    assert format_inr(total_value) == "₹35,400"
    assert format_inr(total_diff, show_sign=True) == "+₹400"
    assert format_pct(overall_return_pct, show_sign=True) == "+1.14%"
    assert format_inr(monthly_sip_total) == "₹5,000"


def test_chart_series_consistency():
    """Verify chart series vectors match instalment count and calculate valid cumulative values."""
    monthly = 2000
    navs = [48.50, 52.00, 54.00, 55.00, 53.95, 50.00, 44.75]
    result = compute_sip(monthly, navs, scenario_name="base")

    assert len(result["month_end_invested"]) == 7
    assert len(result["month_end_values"]) == 7
    assert len(result["gap_per_month"]) == 7

    # Terminal points should match portfolio total
    assert result["month_end_invested"][-1] == 14000
    assert result["month_end_values"][-1] == 12300
    assert result["gap_per_month"][-1] == -1700

    # Month 4 peak: invested ₹8,000, value ₹8,421 (+₹421 gap)
    assert result["month_end_invested"][3] == 8000
    assert result["month_end_values"][3] in (8420, 8421)

    # Most units month: Month 7 (NAV 44.75, ~44.69 units)
    assert result["month_with_most_units"]["month_number"] == 7
    assert result["month_with_most_units"]["units"] == 44.69


def test_indian_rupee_formatting():
    """Test format_inr across single digit, thousands, lakhs, and negative numbers."""
    assert format_inr(0) == "₹0"
    assert format_inr(500) == "₹500"
    assert format_inr(2000) == "₹2,000"
    assert format_inr(14000) == "₹14,000"
    assert format_inr(35400) == "₹35,400"
    assert format_inr(70000) == "₹70,000"
    assert format_inr(123456) == "₹1,23,456"
    assert format_inr(1234567) == "₹12,34,567"
    assert format_inr(-1700) == "-₹1,700"
    assert format_inr(400, show_sign=True) == "+₹400"
    assert format_inr(50.93, decimals=2) == "₹50.93"
    assert format_inr(44.75, decimals=2) == "₹44.75"


def test_static_data_integrity():
    """Verify static constants for Parag Parikh and Fund History horizons."""
    assert PARAG_PARIKH_DATA["invested"] == 21000
    assert PARAG_PARIKH_DATA["value"] == 23100
    assert PARAG_PARIKH_DATA["diff"] == 2100
    assert PARAG_PARIKH_DATA["return_pct"] == 10.0

    # Horizon validation
    horizons = ["7M", "1Y", "3Y", "5Y"]
    for h in horizons:
        assert h in FUND_HISTORY_HORIZONS
        data = FUND_HISTORY_HORIZONS[h]
        assert "points" in data
        assert "summary" in data
        assert "stats" in data
        assert data["stats"]["risk_category"] == "Very High"

    # Quiz validation
    assert FUND_HISTORY_QUIZ["correct_index"] == 1
    assert "higher NAVs" in FUND_HISTORY_QUIZ["options"][1]

