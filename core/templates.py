"""Deterministic template library for SIP Explainer.

Contains verified, deterministic templates for:
1. Standard refusal states (advice, predictions, off-topic, not-sure)
2. Scenario-adaptive Smart Digest templates
3. Standard verified fallback explanations when generative gate fails
"""

from typing import Any

# -----------------------------------------------------------------------------
# Refusal & Redirection Templates
# -----------------------------------------------------------------------------
DECLINE_ADVICE_TEMPLATE = (
    "We provide educational explanations of your SIP numbers, not financial or investment advice. "
    "Your current portfolio has {invested} invested with a current value of {value} ({diff}, {return_pct}). "
    "Whether to continue, stop, or change your SIP depends on your personal financial goals and risk profile.\n\n"
    "For trusted, regulated investor guidance, please consult:\n"
    "• Groww Help Centre: https://groww.in/help\n"
    "• AMFI Investor Education: https://www.amfiindia.com/investor-corner\n"
    "• SEBI Investor Portal: https://investor.sebi.gov.in"
)

DECLINE_PREDICTION_TEMPLATE = (
    "Mutual fund unit prices move with broader market conditions, and future price movements or recovery "
    "timelines cannot be predicted. Your SIP has accumulated {units_total} units across {n_instalments} instalments. "
    "These units remain yours, and your portfolio value will continue to reflect future NAV movements."
)

NOT_SURE_TEMPLATE = (
    "This specific information is not contained in your personal SIP contribution data. "
    "For fund-specific details such as the expense ratio, portfolio holdings, or fund manager background, "
    "please refer to the official scheme factsheet published on the AMC website."
)

REDIRECT_OFFTOPIC_TEMPLATE = (
    "I am your SIP Explainer assistant. I can only explain your mutual fund SIP performance, "
    "unit accumulation, average purchase cost, and return differences."
)

FALLBACK_ANSWER_TEMPLATE = (
    "You have deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
    "Your {units_total} units are currently worth {value} at today's NAV of {nav_now}. "
    "Your average purchase cost is {avg_cost} per unit. A difference between your invested amount "
    "and current value is unrealised on paper until units are sold."
)


# -----------------------------------------------------------------------------
# Scenario-Adaptive Smart Digest Templates
# -----------------------------------------------------------------------------
def get_standard_digest_template(computed: dict[str, Any]) -> dict[str, str]:
    """Return a deterministic, scenario-matched Smart Digest with 3 structured answers."""
    scenario = computed.get("scenario", "base")
    relation = computed.get("relation", "sip_lower")
    diff = computed.get("diff", 0)

    # 1. Base / Falling / Volatile (Loss scenarios)
    if diff < 0:
        if relation == "sip_lower":
            what_happened = (
                "You deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
                "Your {units_total} units are worth {value} at today's NAV of {nav_now}."
            )
            what_explains = (
                "Your average purchase cost is {avg_cost} per unit. Today's NAV is lower than that, "
                "so your value is lower than your invested amount today. Most instalments were bought "
                "when NAV hovered between {nav_low_range} and {nav_high_range}."
            )
            what_to_understand = (
                "A difference only becomes a gain or loss when units are sold. "
                "This is not money disappearing from your account."
            )
        else:  # sip_higher or equal
            what_happened = (
                "You deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
                "Your {units_total} units are worth {value} at today's NAV of {nav_now}."
            )
            what_explains = (
                "The fund dropped {fund_return_pct}, while your personal SIP return was {return_pct}. "
                "Because your monthly instalments bought units as NAV declined, your average cost was "
                "lowered to {avg_cost}, softening the impact compared to a single lumpsum deposit."
            )
            what_to_understand = (
                "A difference only becomes a gain or loss when units are sold. "
                "Accumulating units at lower prices reduces your average cost across market cycles."
            )

    # 2. Gain scenarios (Rising, V-shape, Twelve instalments)
    elif diff > 0:
        if relation == "sip_higher":
            what_happened = (
                "You deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
                "Your {units_total} units are worth {value} at today's NAV of {nav_now}."
            )
            what_explains = (
                "Your SIP return of {return_pct} outpaced the fund's point-to-point return of {fund_return_pct}. "
                "Buying units during lower NAV levels lowered your average cost to {avg_cost}, generating higher gains."
            )
            what_to_understand = (
                "A difference only becomes a gain or loss when units are sold. "
                "Rupee-cost averaging during market fluctuations allows your fixed instalments to accumulate more units."
            )
        else:  # sip_lower or equal
            what_happened = (
                "You deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
                "Your {units_total} units are worth {value} at today's NAV of {nav_now}."
            )
            what_explains = (
                "Your average purchase cost is {avg_cost} per unit, which is below today's NAV of {nav_now}. "
                "Your SIP grew by {return_pct}. The fund's point-to-point return was {fund_return_pct} because earlier "
                "deposits bought at lower prices while later deposits bought at higher prices."
            )
            what_to_understand = (
                "A difference only becomes a gain or loss when units are sold. "
                "Unit accumulation continues across both rising and falling market phases."
            )

    # 3. Flat scenario
    else:
        what_happened = (
            "You deposited {invested} across {n_instalments} monthly instalments of {monthly}. "
            "Your {units_total} units are worth {value} at today's NAV of {nav_now}."
        )
        what_explains = (
            "The fund NAV remained constant at {nav_now} across all your instalments. "
            "Your average cost equals current NAV, and your portfolio value equals your total contributions."
        )
        what_to_understand = (
            "When NAV does not fluctuate, fixed monthly deposits accumulate units at an even rate "
            "without creating unrealised gains or losses."
        )

    # Fill placeholders
    formatted = computed["formatted"]
    return {
        "what_happened": what_happened.format(**formatted),
        "what_explains": what_explains.format(**formatted),
        "what_to_understand": what_to_understand.format(**formatted),
    }


def hydrate_template(template_str: str, formatted: dict[str, str]) -> str:
    """Safely format a template string with computed formatted values."""
    try:
        return template_str.format(**formatted)
    except KeyError:
        # Fallback for safe interpolation
        res = template_str
        for k, v in formatted.items():
            res = res.replace(f"{{{k}}}", str(v))
        return res

