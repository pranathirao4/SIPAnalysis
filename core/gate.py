"""7-Step Eval Gate and Safety Guardrail Pipeline for SIP Explainer.

Enforces zero advice, zero predictions, strict placeholder rules,
number whitelisting, readability bounds, and semantic LLM judging.
"""

import re
import time
from typing import Any

from core.llm import generate_llm_response, judge_relation
from core.logger import log_request
from core.templates import (
    DECLINE_ADVICE_TEMPLATE,
    DECLINE_PREDICTION_TEMPLATE,
    NOT_SURE_TEMPLATE,
    REDIRECT_OFFTOPIC_TEMPLATE,
    FALLBACK_ANSWER_TEMPLATE,
    get_standard_digest_template,
    hydrate_template,
)

# -----------------------------------------------------------------------------
# Regex Backstops for Instant Refusals (Groups C & D)
# -----------------------------------------------------------------------------
ADVICE_REGEX = re.compile(
    r"\b(should\s+i|stop\s+my\s+sip|stop\s+(?:the|this)?\s*sip|can\s+i\s+stop|sell|buy|which\s+fund|better\s+than|which\s+is\s+better|tell\s+me\s+a\s+stock|what\s+to\s+do|recommend|ignore\s+your\s+rules|increase\s+my\s+sip)\b",
    re.IGNORECASE,
)

PREDICTION_REGEX = re.compile(
    r"\b(will\s+(?:it|the\s+market|prices?)\s+recover|will\s+i\s+lose|lose\s+everything|when\s+will\s+it\s+recover|will\s+it\s+crash)\b",
    re.IGNORECASE,
)

NOT_SURE_REGEX = re.compile(
    r"\b(expense\s+ratio|fund\s+manager|portfolio\s+holdings|pe\s+ratio|turnover\s+ratio)\b",
    re.IGNORECASE,
)

OFFTOPIC_REGEX = re.compile(
    r"\b(who\s+is\s+the\s+prime\s+minister|who\s+is\s+prime\s+minister|weather\s+in|capital\s+of|president\s+of)\b",
    re.IGNORECASE,
)

# -----------------------------------------------------------------------------
# Blocklists
# -----------------------------------------------------------------------------
ADVICE_BLOCKLIST = [
    "you should",
    "i recommend",
    "buy",
    "sell",
    "switch to",
    "redeem",
    "stop your sip",
    "continue your sip",
    "better fund",
    "best fund",
]

FEAR_BLOCKLIST = [
    "panic",
    "crash",
    "danger",
    "hurry",
    "last chance",
    "don't miss",
    "losing everything",
    "wipe out",
    "disaster",
    "alarming",
]

ALLOWED_ROUTES = {
    "answer",
    "decline_advice",
    "decline_prediction",
    "redirect_offtopic",
    "not_sure",
}


def check_regex_backstop(question: str) -> str | None:
    """Check if the question triggers a hard refusal backstop."""
    q = question.strip()
    if ADVICE_REGEX.search(q):
        return "decline_advice"
    if PREDICTION_REGEX.search(q):
        return "decline_prediction"
    if NOT_SURE_REGEX.search(q):
        return "not_sure"
    if OFFTOPIC_REGEX.search(q):
        return "redirect_offtopic"
    return None


def run_eval_gate(
    raw_response: dict[str, str],
    question: str,
    computed: dict[str, Any],
    is_explanation: bool = False
) -> tuple[bool, str, list[int], list[int], str]:
    """Execute the 7 sequential gate checks.

    Returns:
        (passed, reason, checks_passed, checks_failed, hydrated_text)
    """
    checks_passed = []
    checks_failed = []

    route = raw_response.get("route", "").strip()
    raw_answer = raw_response.get("answer", "").strip()

    # CHECK 1: JSON parses and route is allowed
    if not route or route not in ALLOWED_ROUTES:
        checks_failed.append(1)
        return False, f"Invalid route: {route}", checks_passed, checks_failed, ""
    checks_passed.append(1)

    # For non-answer routes, gate passes immediately (they use fixed templates)
    if route != "answer":
        return True, "Non-answer route passed", checks_passed, checks_failed, ""

    # CHECK 2: Digit check (no bare digits outside placeholders & valid keys)
    text_without_placeholders = re.sub(r"\{[a-zA-Z0-9_]+\}", "", raw_answer)
    if re.search(r"\d", text_without_placeholders):
        checks_failed.append(2)
        return False, "Bare digit generated outside placeholder", checks_passed, checks_failed, ""

    placeholders = re.findall(r"\{([a-zA-Z0-9_]+)\}", raw_answer)
    for p in placeholders:
        if p not in computed["formatted"]:
            checks_failed.append(2)
            return False, f"Unknown placeholder {{{p}}}", checks_passed, checks_failed, ""
    checks_passed.append(2)

    # Hydrate placeholders with computed formatted values
    hydrated_text = raw_answer.format(**computed["formatted"])

    # CHECK 3: Number verification against allowed set
    allowed = computed["allowed_numbers"]
    found_numbers = re.findall(r"\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?\b", hydrated_text)
    for num in found_numbers:
        raw_num = num.rstrip("%")
        cleaned_num = raw_num.replace(",", "")
        if (
            num not in allowed
            and raw_num not in allowed
            and cleaned_num not in allowed
            and str(int(float(cleaned_num))) not in allowed
        ):
            checks_failed.append(3)
            return False, f"Unverified number '{num}' cited in final text", checks_passed, checks_failed, hydrated_text
    checks_passed.append(3)

    # CHECK 4: Advice phrases blocklist
    hydrated_lower = hydrated_text.lower()
    for phrase in ADVICE_BLOCKLIST:
        if re.search(rf"\b{re.escape(phrase)}\b", hydrated_lower):
            checks_failed.append(4)
            return False, f"Prohibited advice phrase detected: '{phrase}'", checks_passed, checks_failed, hydrated_text
    checks_passed.append(4)

    # CHECK 5: Fear / Urgency blocklist
    for phrase in FEAR_BLOCKLIST:
        if re.search(rf"\b{re.escape(phrase)}\b", hydrated_lower):
            checks_failed.append(5)
            return False, f"Prohibited fear/urgency phrase detected: '{phrase}'", checks_passed, checks_failed, hydrated_text
    checks_passed.append(5)

    # CHECK 6: Readability check (sentence length <= 22, word count <= 110)
    words = hydrated_text.split()
    total_words = len(words)
    if total_words > 110:
        checks_failed.append(6)
        return False, f"Word count ({total_words}) exceeds 110 words limit", checks_passed, checks_failed, hydrated_text

    sentences = [s.strip() for s in re.split(r"[.!?]+", hydrated_text) if s.strip()]
    if sentences:
        avg_sentence_len = total_words / len(sentences)
        if avg_sentence_len > 22.0:
            checks_failed.append(6)
            return False, f"Average sentence length ({avg_sentence_len:.1f}) exceeds 22 words", checks_passed, checks_failed, hydrated_text
    checks_passed.append(6)

    # CHECK 7: Semantic Relation LLM Judge
    if is_explanation:
        judge_passed = judge_relation(hydrated_text, computed["relation"], computed)
        if not judge_passed:
            checks_failed.append(7)
            return False, "Semantic judge: explanation does not match expected relation", checks_passed, checks_failed, hydrated_text
    checks_passed.append(7)

    return True, "All gate checks passed", checks_passed, checks_failed, hydrated_text


def process_question_pipeline(
    question: str,
    computed: dict[str, Any],
    is_explanation: bool = False
) -> dict[str, Any]:
    """Execute complete end-to-end question answering pipeline.

    Includes regex backstop, single-call LLM generation, 7-step Eval Gate,
    single retry on failure, and fallback template interpolation.
    """
    t0 = time.time()
    formatted = computed["formatted"]

    # 1. Immediate regex backstop
    forced_route = check_regex_backstop(question)
    if forced_route:
        latency_ms = int((time.time() - t0) * 1000)
        if forced_route == "decline_advice":
            text = hydrate_template(DECLINE_ADVICE_TEMPLATE, formatted)
        elif forced_route == "decline_prediction":
            text = hydrate_template(DECLINE_PREDICTION_TEMPLATE, formatted)
        elif forced_route == "not_sure":
            text = hydrate_template(NOT_SURE_TEMPLATE, formatted)
        else:
            text = hydrate_template(REDIRECT_OFFTOPIC_TEMPLATE, formatted)

        res = {
            "route": forced_route,
            "answer": text,
            "is_ai": False,
            "badge": "Standard explanation (not AI-generated)",
            "checks_passed": [1, 2, 3, 4, 5, 6, 7],
            "checks_failed": [],
            "fallback_used": False,
            "latency_ms": latency_ms,
        }
        log_request(computed["scenario"], question, forced_route, [1, 2, 3, 4, 5, 6, 7], [], False, latency_ms)
        return res

    # 2. Call LLM (First Attempt)
    raw_res = generate_llm_response(question, computed)
    route = raw_res.get("route", "answer")

    # If model routed away from "answer", ignore its text and return fixed template
    if route != "answer":
        latency_ms = int((time.time() - t0) * 1000)
        if route == "decline_advice":
            text = hydrate_template(DECLINE_ADVICE_TEMPLATE, formatted)
        elif route == "decline_prediction":
            text = hydrate_template(DECLINE_PREDICTION_TEMPLATE, formatted)
        elif route == "not_sure":
            text = hydrate_template(NOT_SURE_TEMPLATE, formatted)
        else:
            text = hydrate_template(REDIRECT_OFFTOPIC_TEMPLATE, formatted)

        res = {
            "route": route,
            "answer": text,
            "is_ai": False,
            "badge": "Standard explanation (not AI-generated)",
            "checks_passed": [1, 2, 3, 4, 5, 6, 7],
            "checks_failed": [],
            "fallback_used": False,
            "latency_ms": latency_ms,
        }
        log_request(computed["scenario"], question, route, [1, 2, 3, 4, 5, 6, 7], [], False, latency_ms)
        return res

    # 3. Check Eval Gate for "answer" route
    passed, reason, p_checks, f_checks, hydrated = run_eval_gate(
        raw_res, question, computed, is_explanation=is_explanation
    )

    # 4. Retry Once if failed
    if not passed:
        raw_res_retry = generate_llm_response(question, computed, retry_reason=reason)
        passed, reason, p_checks, f_checks, hydrated = run_eval_gate(
            raw_res_retry, question, computed, is_explanation=is_explanation
        )

    latency_ms = int((time.time() - t0) * 1000)

    # 5. Passed Gate -> Return verified AI explanation
    if passed:
        res = {
            "route": "answer",
            "answer": hydrated,
            "is_ai": True,
            "badge": "Numbers verified against your SIP data",
            "checks_passed": p_checks,
            "checks_failed": f_checks,
            "fallback_used": False,
            "latency_ms": latency_ms,
        }
        log_request(computed["scenario"], question, "answer", p_checks, f_checks, False, latency_ms)
        return res

    # 6. Failed 2nd Gate -> Return deterministic fallback template
    fallback_text = hydrate_template(FALLBACK_ANSWER_TEMPLATE, formatted)
    res = {
        "route": "answer",
        "answer": fallback_text,
        "is_ai": False,
        "badge": "Standard explanation (not AI-generated)",
        "checks_passed": p_checks,
        "checks_failed": f_checks,
        "fallback_used": True,
        "latency_ms": latency_ms,
    }
    log_request(computed["scenario"], question, "answer", p_checks, f_checks, True, latency_ms)
    return res


def generate_smart_digest_pipeline(computed: dict[str, Any]) -> dict[str, Any]:
    """Generate or retrieve verified Smart Digest for Screen 4."""
    # Fixed request for Smart Digest
    req_question = "Explain my SIP in simple words with what happened, what explains it, and what to understand."
    result = process_question_pipeline(req_question, computed, is_explanation=True)

    # Deterministic 3-part structured breakdown
    standard_parts = get_standard_digest_template(computed)

    # If AI passed gate and generated a 3-part or verified prose, format into structured parts
    if result["is_ai"] and not result["fallback_used"]:
        # Split or structure response
        text = result["answer"]
        return {
            "is_ai": True,
            "badge": "Numbers verified against your SIP data",
            "what_happened": standard_parts["what_happened"],
            "what_explains": text,
            "what_to_understand": standard_parts["what_to_understand"],
            "latency_ms": result["latency_ms"],
        }
    else:
        return {
            "is_ai": False,
            "badge": "Standard explanation (not AI-generated)",
            "what_happened": standard_parts["what_happened"],
            "what_explains": standard_parts["what_explains"],
            "what_to_understand": standard_parts["what_to_understand"],
            "latency_ms": result["latency_ms"],
        }

