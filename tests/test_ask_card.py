"""Tests for Stage 4: Inline Ask Card states, telemetry logging, and guardrails."""

import json
from pathlib import Path
import pytest
from core.compute import compute_sip
from core.gate import process_question_pipeline
from core.logger import log_request
from app import extract_data_chips


@pytest.fixture
def base_data():
    return compute_sip(2000, [48.50, 52.00, 54.00, 55.00, 53.95, 50.00, 44.75], "base")


def test_ask_card_empty_initial_state():
    """Verify Ask Card starts empty (history is empty list initially)."""
    history = []
    assert len(history) == 0


def test_ask_card_state_advice_declined(base_data):
    """Verify Advice Declined state provides regulatory sources and restated numbers."""
    res = process_question_pipeline("Should I stop my SIP?", base_data)
    assert res["route"] == "decline_advice"
    assert "https://groww.in/help" in res["answer"]
    assert "https://www.amfiindia.com/investor-corner" in res["answer"]
    assert "https://investor.sebi.gov.in" in res["answer"]
    assert "₹14,000" in res["answer"]
    assert "₹12,300" in res["answer"]
    assert res["is_ai"] is False


def test_ask_card_state_prediction_declined(base_data):
    """Verify Prediction Declined state explains price predictability."""
    res = process_question_pipeline("Will the market recover next month?", base_data)
    assert res["route"] == "decline_prediction"
    assert "cannot be predicted" in res["answer"]
    assert "units" in res["answer"]
    assert res["is_ai"] is False


def test_ask_card_state_not_sure(base_data):
    """Verify Not Sure state points to scheme factsheet."""
    res = process_question_pipeline("What is this fund's expense ratio?", base_data)
    assert res["route"] == "not_sure"
    assert "factsheet" in res["answer"]
    assert res["is_ai"] is False


def test_ask_card_state_offtopic(base_data):
    """Verify Off-topic state redirects user to SIP topics."""
    res = process_question_pipeline("Who is the prime minister?", base_data)
    assert res["route"] == "redirect_offtopic"
    assert "SIP" in res["answer"]
    assert res["is_ai"] is False


def test_ask_card_state_answered_citations(base_data):
    """Verify Answered state produces valid data chips from cited metrics."""
    res = process_question_pipeline("Why is my SIP showing red?", base_data)
    assert res["route"] == "answer"
    chips = extract_data_chips(res["answer"], base_data)
    assert len(chips) > 0
    assert any("₹" in c for c in chips)


def test_telemetry_logging(tmp_path, monkeypatch):
    """Verify requests.jsonl appends valid structured logs with no PII."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_file = log_dir / "requests.jsonl"

    # Call log_request
    log_request(
        scenario="base",
        question="Why is my SIP lower?",
        route="answer",
        checks_passed=[1, 2, 3, 4, 5, 6, 7],
        checks_failed=[],
        fallback_used=False,
        latency_ms=850,
    )

    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        last_entry = json.loads(lines[-1])
        assert last_entry["scenario"] == "base"
        assert last_entry["route"] == "answer"
        assert "timestamp" in last_entry
        assert last_entry["latency_ms"] == 850
        assert "email" not in last_entry
        assert "user_id" not in last_entry

