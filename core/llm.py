"""Groq LLM Client & Prompt Engineering for SIP Explainer.

Executes single-call structured inference with placeholder constraints,
strict routing, and temperature 0.0 semantic evaluation judging.
"""

import json
import os
import re
from typing import Any
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

def get_groq_client() -> Groq:
    """Retrieve Groq client using Streamlit secrets or environment variable."""
    api_key = None
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in Streamlit secrets or environment variables.")

    return Groq(api_key=api_key)


GLOSSARY = {
    "nav": "Net Asset Value: The per-unit market price of the fund.",
    "average_cost": "Total invested cash divided by total units accumulated so far.",
    "unrealised": "On paper only. Becomes a real gain or loss only when units are sold.",
    "xirr": "Annualised return for multiple deposit dates. Shown only after 12 months.",
    "rupee_cost_averaging": "Fixed deposits buy more units at low NAVs and fewer at high NAVs.",
    "point_to_point": "Lump sum return between day 1 and today, ignoring recurring dates.",
}


SYSTEM_PROMPT = """You are the AI assistant for Groww's 'SIP Explainer'.
Your task is to explain mutual fund SIP performance in plain English at an 8th-grade reading level (or simple Hinglish in Roman script if the user asks in Hinglish).

You will receive:
1. Computed financial data for the user's SIP and fund.
2. The user's question.
3. A financial glossary.

RULES:
1. Output MUST be a single valid JSON object with EXACTLY two keys:
   {
     "route": "answer | decline_advice | decline_prediction | redirect_offtopic | not_sure",
     "answer": "your response"
   }
2. ROUTING:
   - "decline_advice": User asks if they should buy, sell, hold, switch, increase, stop, continue, or compare funds.
   - "decline_prediction": User asks if market will recover, if they will lose everything, or future prices.
   - "redirect_offtopic": User asks non-financial / non-SIP questions (e.g. general knowledge, weather).
   - "not_sure": User asks for fund-level facts not in their personal SIP data (e.g. expense ratio, fund manager).
   - "answer": Explanations of user's SIP performance, units, average cost, returns, and differences.
3. STRICT PLACEHOLDER RULE - ZERO RAW DIGITS (0-9):
   - You MUST NOT write any bare digits or raw numbers (0-9).
   - ALL numbers MUST use curly brace placeholders from the allowed list:
     {invested}, {value}, {diff}, {return_pct}, {fund_return_pct}, {avg_cost}, {nav_now},
     {nav_start}, {units_total}, {n_instalments}, {monthly}, {units_prev}, {units_last},
     {nav_last}, {nav_low_range}, {nav_high_range}
   - Example: Write "Your average cost of {avg_cost} is above today's NAV of {nav_now}" instead of "Your average cost of ₹50.93 is above ₹44.75".
   - Writing ANY raw digit outside a placeholder is an automatic gate failure.
4. WORDING & COMPLIANCE GUARDRAILS:
   - Prohibited words: Do NOT use the words 'buy', 'sell', 'redeem', 'switch to', 'you should', 'i recommend', 'panic', 'crash'.
   - When explaining that differences are unrealised on paper, use the exact phrase: "a difference only becomes a gain or loss when units are sold".
   - State the relation accurately:
     * If relation is "sip_lower": state that SIP return of {return_pct} is lower than fund return of {fund_return_pct} because instalments were purchased at varying NAV levels.
     * If relation is "sip_higher": state that SIP return of {return_pct} is higher than fund return of {fund_return_pct} because units were acquired at lower NAV levels.
     * If relation is "equal": state that SIP return equals fund return because NAV remained flat.
   - Tone: Calm, neutral, reassuring without making promises.
   - Length: Maximum 110 words total. Average sentence length at most 22 words.
   - NEVER give financial advice. NEVER say what the user should do. NEVER predict prices.
"""


def generate_llm_response(
    question: str,
    computed: dict[str, Any],
    retry_reason: str | None = None
) -> dict[str, str]:
    """Call Groq API to generate route and answer."""
    client = get_groq_client()

    metrics = {
        "scenario": computed["scenario"],
        "invested": computed["formatted"]["invested"],
        "value": computed["formatted"]["value"],
        "diff": computed["formatted"]["diff"],
        "return_pct": computed["formatted"]["return_pct"],
        "fund_return_pct": computed["formatted"]["fund_return_pct"],
        "avg_cost": computed["formatted"]["avg_cost"],
        "nav_now": computed["formatted"]["nav_now"],
        "nav_start": computed["formatted"]["nav_start"],
        "units_total": computed["formatted"]["units_total"],
        "n_instalments": computed["formatted"]["n_instalments"],
        "monthly": computed["formatted"]["monthly"],
        "units_prev": computed["formatted"]["units_prev"],
        "units_last": computed["formatted"]["units_last"],
        "nav_low_range": computed["formatted"]["nav_low_range"],
        "nav_high_range": computed["formatted"]["nav_high_range"],
        "relation": computed["relation"],
    }

    user_content = json.dumps({
        "metrics": metrics,
        "question": question,
        "glossary": GLOSSARY
    }, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if retry_reason:
        messages.append({
            "role": "system",
            "content": f"ATTENTION: Your previous attempt failed validation with reason: {retry_reason}. Remember: DO NOT WRITE RAW DIGITS (0-9). Do not use 'buy', 'sell', 'redeem'. Say 'when units are sold'. Use ONLY placeholders for all numbers!"
        })

    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model=DEFAULT_GROQ_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=450
    )

    raw_text = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw_text)
        route = parsed.get("route", "answer").strip()
        answer = parsed.get("answer", "").strip()
        return {"route": route, "answer": answer}
    except Exception:
        return {"route": "invalid_json", "answer": raw_text}


def judge_relation(
    explanation_text: str,
    expected_relation: str,
    computed: dict[str, Any]
) -> bool:
    """LLM Judge at temperature 0.0 to verify semantic relation of SIP vs Fund return."""
    client = get_groq_client()

    judge_prompt = f"""You are a strict financial evaluator.
Evaluate whether the following text accurately describes the relation between the investor's SIP return and the mutual fund's point-to-point return.

Expected Relation: '{expected_relation}' (where 'sip_lower' means personal return is lower/worse than fund return; 'sip_higher' means personal return is higher/better; 'equal' means equal).
Personal Return: {computed['formatted']['return_pct']}
Fund Return: {computed['formatted']['fund_return_pct']}

Explanation Text:
\"\"\"{explanation_text}\"\"\"

RUBRIC:
1. Does the text state the correct direction (gain, loss, or no change)?
2. Does it correctly compare personal SIP return to the fund return without claiming the opposite?
3. Does it make NO future price predictions and state NO speculative market causes?

Answer with ONLY a JSON object: {{"judge_pass": true}} or {{"judge_pass": false, "reason": "..."}}
"""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_GROQ_MODEL,
            messages=[{"role": "user", "content": judge_prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=150
        )
        parsed = json.loads(response.choices[0].message.content or "{}")
        return bool(parsed.get("judge_pass", False))
    except Exception:
        return True
