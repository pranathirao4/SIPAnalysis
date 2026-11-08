"""Telemetry and Request Logger for SIP Explainer.

Appends structured JSON records to logs/requests.jsonl with zero PII.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def log_request(
    scenario: str,
    question: str,
    route: str,
    checks_passed: list[int],
    checks_failed: list[int],
    fallback_used: bool,
    latency_ms: int,
) -> None:
    """Append one structured telemetry log entry to logs/requests.jsonl."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "requests.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenario": scenario,
        "question": question,
        "route": route,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "fallback_used": fallback_used,
        "latency_ms": latency_ms,
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        # Non-blocking logging failure
        print(f"Failed to write log: {e}")

