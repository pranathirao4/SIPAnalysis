"""Tests for Stage 2 UI screens, routing logic, and data reconciliation."""

import pytest
from core.compute import compute_sip, format_inr, format_pct
from core.static_data import (
    PARAG_PARIKH_DATA,
    AXIS_BLUECHIP_METADATA,
    FUND_HISTORY_HORIZONS,
    FUND_HISTORY_QUIZ,
    LEARN_GRAPH_ITEMS,
    FUND_HISTORY_TAKEAWAYS,
)
from app import BASE_AXIS_COMPUTE, SCENARIOS


def test_base_axis_numbers_consistency():
    """Verify base Axis Bluechip numbers across all screens:
    ₹12,300, -₹1,700, -12.14%, 274.86 units, ₹50.93 avg cost, ₹44.75 today NAV."""
    b = BASE_AXIS_COMPUTE
    assert b["value"] == 12300
    assert b["diff"] == -1700
    assert b["return_pct"] == -12.14
    assert b["units_total"] == 274.86
    assert b["avg_cost"] == 50.93
    assert b["nav_now"] == 44.75
    assert b["invested"] == 14000
    assert b["fund_return_pct"] == -7.73

    # Check formatted representation
    assert b["formatted"]["value"] == "₹12,300"
    assert b["formatted"]["diff"] == "-₹1,700"
    assert b["formatted"]["return_pct"] == "-12.14%"
    assert b["formatted"]["units_total"] == "274.86"
    assert b["formatted"]["avg_cost"] == "₹50.93"
    assert b["formatted"]["nav_now"] == "₹44.75"


def test_parag_parikh_numbers_consistency():
    """Verify Parag Parikh static numbers: ₹23,100, +₹2,100, +10.0%, ₹21,000."""
    pp = PARAG_PARIKH_DATA
    assert pp["invested"] == 21000
    assert pp["value"] == 23100
    assert pp["diff"] == 2100
    assert pp["return_pct"] == 10.0
    assert format_inr(pp["value"]) == "₹23,100"
    assert format_inr(pp["diff"], show_sign=True) == "+₹2,100"
    assert pp["return_display"] == "+10.00%"


def test_home_screen_reconciliation():
    """Verify Home totals: ₹35,000 invested, ₹35,400 value, +₹400 (+1.14%)."""
    tot_invested = BASE_AXIS_COMPUTE["invested"] + PARAG_PARIKH_DATA["invested"]
    tot_value = BASE_AXIS_COMPUTE["value"] + PARAG_PARIKH_DATA["value"]
    tot_diff = tot_value - tot_invested
    tot_ret = round((tot_diff / tot_invested) * 100, 2)
    tot_monthly = BASE_AXIS_COMPUTE["monthly"] + PARAG_PARIKH_DATA["monthly_amount"]

    assert tot_invested == 35000
    assert tot_value == 35400
    assert tot_diff == 400
    assert tot_ret == 1.14
    assert tot_monthly == 5000

    assert format_inr(tot_invested) == "₹35,000"
    assert format_inr(tot_value) == "₹35,400"
    assert format_inr(tot_diff, show_sign=True) == "+₹400"
    assert format_pct(tot_ret, show_sign=True) == "+1.14%"


def test_fund_history_static_compliance():
    """Verify Fund History has no AI claims and provides all 4 required horizons."""
    assert "7M" in FUND_HISTORY_HORIZONS
    assert "1Y" in FUND_HISTORY_HORIZONS
    assert "3Y" in FUND_HISTORY_HORIZONS
    assert "5Y" in FUND_HISTORY_HORIZONS

    for h, data in FUND_HISTORY_HORIZONS.items():
        # Ensure summaries and stats are present
        assert "summary" in data and len(data["summary"]) > 20
        assert "stats" in data
        assert "buttons" in data and len(data["buttons"]) >= 2
        assert data["stats"]["risk_category"] == "Very High"
        # Confirm no CRISIL rating string is present in stats
        for val in data["stats"].values():
            assert "CRISIL" not in val

    # Verify Quiz Data
    assert FUND_HISTORY_QUIZ["correct_index"] == 1
    assert "higher NAVs" in FUND_HISTORY_QUIZ["options"][1]
    assert "7 different prices" in FUND_HISTORY_QUIZ["explanation"]


def test_tester_mode_scenario_computations():
    """Verify that changing tester mode scenario recomputes correctly."""
    for sc_name, sc_data in SCENARIOS.items():
        res = compute_sip(sc_data["monthly"], sc_data["navs"], sc_name)
        assert res["invested"] > 0
        assert res["units_total"] > 0
        assert res["relation"] in ("sip_lower", "sip_higher", "equal")

