"""Static data module for SIP Explainer.

Contains constants for Parag Parikh Flexi Cap Fund, multi-horizon historical
data for Axis Bluechip Fund, quiz items, and educational fund fundamentals.
This data is purely deterministic and involves zero live AI calls.
"""

# Parag Parikh Flexi Cap Fund static constants
PARAG_PARIKH_DATA = {
    "name": "Parag Parikh Flexi Cap Fund",
    "short_name": "Parag Parikh",
    "icon": "PP",
    "monthly_amount": 3000,
    "n_instalments": 7,
    "invested": 21000,
    "value": 23100,
    "diff": 2100,
    "return_pct": 10.00,
    "return_display": "+10.00%",
    "pill_text": "+₹2,100 (+10.0%)",
    "schedule": "Last instalment 5 Nov ✓ · Next 5 Dec",
    "status": "Active SIP",
    "tag": "Unrealised gain",
    "mvp_note": "Detailed analysis is available for Axis Bluechip in this MVP",
}

# Axis Bluechip Fund static metadata
AXIS_BLUECHIP_METADATA = {
    "name": "Axis Bluechip Fund",
    "short_name": "Axis Bluechip",
    "icon": "AB",
    "plan": "Direct · Growth",
    "monthly_default": 2000,
    "schedule": "Last instalment 5 Nov ✓ · Next 5 Dec",
    "status": "Active SIP",
    "tag": "Unrealised difference",
}

# Multi-horizon Fund Historical Performance for Screen 5
FUND_HISTORY_HORIZONS = {
    "7M": {
        "label": "Since you started (7M)",
        "window_name": "Since you started (7M)",
        "x_labels": ["May", "Aug", "Nov"],
        "y_range": [44, 50, 56],
        "points": [
            {"date": "May", "nav": 48.50, "label": "₹48.50"},
            {"date": "Aug", "nav": 55.00, "label": "Peak ₹55.00"},
            {"date": "Nov", "nav": 44.75, "label": "₹44.75"},
        ],
        "all_dates": ["May '23", "Jun '23", "Jul '23", "Aug '23", "Sep '23", "Oct '23", "Nov '23"],
        "all_navs": [48.50, 52.00, 54.00, 55.00, 53.95, 50.00, 44.75],
        "buttons": [
            {
                "id": "growth",
                "label": "+13.4% rally (May to Aug)",
                "desc": "Market prices moved up and down during this period.",
                "highlight_range": [0, 3],
            },
            {
                "id": "decline",
                "label": "-18.6% dip (Aug to Nov)",
                "desc": "Market prices moved up and down during this period.",
                "highlight_range": [3, 6],
            },
        ],
        "summary": (
            "Since you started in May, Axis Bluechip's NAV moved from ₹48.50 to ₹44.75 (-7.73%). "
            "It rose to ₹55.00 in August, then fell to ₹44.75 by November.\n\n"
            "Your SIP return (-12.14%) is lower than the fund's (-7.73%) because most of your instalments "
            "(June to October) were bought at NAVs between ₹50.00 and ₹55.00, higher than the NAV when you "
            "started and higher than today's ₹44.75."
        ),
        "patterns": [
            {
                "type": "rally",
                "title": "+13.4% in 3 months",
                "subtitle": "May to Aug, ₹48.50 to ₹55.00",
                "note": "Market prices moved up and down during this period.",
            },
            {
                "type": "correction",
                "title": "-18.6% in 3 months",
                "subtitle": "Aug to Nov, ₹55.00 to ₹44.75",
                "note": "Market prices moved up and down during this period.",
            },
        ],
        "stats": {
            "start_nav": "₹48.50",
            "start_nav_sub": "May '23 baseline",
            "current_nav": "₹44.75",
            "current_nav_sub": "November cut-off",
            "period_return": "-7.73%",
            "period_return_sub": "Absolute change",
            "max_drawdown": "-18.6%",
            "max_drawdown_sub": "Peak to trough",
            "benchmark": "-3.5%",
            "benchmark_sub": "Nifty 50 (sample)",
            "risk_category": "Very High",
            "risk_sub": "SEBI Standard",
        },
    },
    "1Y": {
        "label": "1Y",
        "window_name": "1Y View",
        "x_labels": ["Nov'22", "Feb'23", "May'23", "Aug'23", "Nov'23"],
        "y_range": [40, 50, 60],
        "points": [
            {"date": "Nov'22", "nav": 46.00, "label": "₹46.00"},
            {"date": "Feb'23", "nav": 49.50, "label": "₹49.50"},
            {"date": "May'23", "nav": 48.50, "label": "₹48.50"},
            {"date": "Aug'23", "nav": 55.00, "label": "Peak ₹55.00"},
            {"date": "Nov'23", "nav": 44.75, "label": "₹44.75"},
        ],
        "buttons": [
            {
                "id": "growth",
                "label": "+19.6% rally (Nov'22 to Aug'23)",
                "desc": "Market prices moved up and down during this period.",
            },
            {
                "id": "decline",
                "label": "-18.6% dip (Aug to Nov'23)",
                "desc": "Market prices moved up and down during this period.",
            },
        ],
        "summary": (
            "Over the last year, Axis Bluechip's NAV moved from ₹46.00 to ₹44.75 (-2.72%). "
            "It rose to ₹55.00 in August, then fell back to ₹44.75 by November. "
            "This view is about the fund only. It does not depend on when you invested."
        ),
        "patterns": [
            {
                "type": "rally",
                "title": "+19.6% in 9 months",
                "subtitle": "Nov'22 to Aug'23, ₹46.00 to ₹55.00",
                "note": "Market prices moved up and down during this period.",
            },
            {
                "type": "correction",
                "title": "-18.6% in 3 months",
                "subtitle": "Aug to Nov'23, ₹55.00 to ₹44.75",
                "note": "Market prices moved up and down during this period.",
            },
        ],
        "stats": {
            "start_nav": "₹46.00",
            "start_nav_sub": "Nov '22 baseline",
            "current_nav": "₹44.75",
            "current_nav_sub": "November cut-off",
            "period_return": "-2.72%",
            "period_return_sub": "Absolute change",
            "max_drawdown": "-18.6%",
            "max_drawdown_sub": "Peak to trough",
            "benchmark": "+2.0%",
            "benchmark_sub": "Nifty 50 (sample)",
            "risk_category": "Very High",
            "risk_sub": "SEBI Standard",
        },
    },
    "3Y": {
        "label": "3Y",
        "window_name": "3Y View",
        "x_labels": ["Nov '20", "Nov '21", "Nov '22", "Nov '23"],
        "y_range": [25, 40, 55],
        "points": [
            {"date": "Nov '20", "nav": 30.00, "label": "₹30.00"},
            {"date": "Nov '21", "nav": 42.00, "label": "₹42.00"},
            {"date": "Jun '22", "nav": 38.00, "label": "₹38.00"},
            {"date": "Nov '22", "nav": 46.00, "label": "₹46.00"},
            {"date": "Aug '23", "nav": 55.00, "label": "Peak ₹55.00"},
            {"date": "Nov '23", "nav": 44.75, "label": "₹44.75"},
        ],
        "buttons": [
            {
                "id": "growth",
                "label": "+40.0% rally (Nov'20 to Nov'21)",
                "desc": "Market prices moved up and down during this period.",
            },
            {
                "id": "decline",
                "label": "-18.6% dip (Aug to Nov'23)",
                "desc": "Market prices moved up and down during this period.",
            },
        ],
        "summary": (
            "Over three years, NAV moved from ₹30.00 to ₹44.75 (+49.17%, about 14.3% a year). "
            "The path was uneven: it rose through 2021, dipped in mid-2022 and peaked at ₹55.00 in August 2023 "
            "before the latest fall. This view is about the fund only."
        ),
        "patterns": [
            {
                "type": "rally",
                "title": "+40.0% in 12 months",
                "subtitle": "Nov'20 to Nov'21, ₹30.00 to ₹42.00",
                "note": "Market prices moved up and down during this period.",
            },
            {
                "type": "correction",
                "title": "-18.6% in 3 months",
                "subtitle": "Aug to Nov'23, ₹55.00 to ₹44.75",
                "note": "Market prices moved up and down during this period.",
            },
        ],
        "stats": {
            "start_nav": "₹30.00",
            "start_nav_sub": "Nov '20 baseline",
            "current_nav": "₹44.75",
            "current_nav_sub": "November cut-off",
            "period_return": "+49.17%",
            "period_return_sub": "about 14.3% a year",
            "max_drawdown": "-18.6%",
            "max_drawdown_sub": "Peak to trough",
            "benchmark": "+55.0%",
            "benchmark_sub": "Nifty 50 (sample)",
            "risk_category": "Very High",
            "risk_sub": "SEBI Standard",
        },
    },
    "5Y": {
        "label": "5Y",
        "window_name": "5Y View",
        "x_labels": ["Nov '18", "Nov '20", "Nov '22", "Nov '23"],
        "y_range": [20, 40, 60],
        "points": [
            {"date": "Nov '18", "nav": 33.00, "label": "₹33.00"},
            {"date": "Mar '20", "nav": 22.00, "label": "₹22.00"},
            {"date": "Nov '20", "nav": 30.00, "label": "₹30.00"},
            {"date": "Nov '21", "nav": 42.00, "label": "₹42.00"},
            {"date": "Jun '22", "nav": 38.00, "label": "₹38.00"},
            {"date": "Nov '22", "nav": 46.00, "label": "₹46.00"},
            {"date": "Aug '23", "nav": 55.00, "label": "Peak ₹55.00"},
            {"date": "Nov '23", "nav": 44.75, "label": "₹44.75"},
        ],
        "buttons": [
            {
                "id": "growth",
                "label": "+90.9% rally (Mar'20 to Nov'21)",
                "desc": "Market prices moved up and down during this period.",
            },
            {
                "id": "decline",
                "label": "-33.3% dip (Nov'18 to Mar'20)",
                "desc": "Market prices moved up and down during this period.",
            },
        ],
        "summary": (
            "Over five years, NAV moved from ₹33.00 to ₹44.75 (+35.61%, about 6.3% a year). "
            "It fell to ₹22.00 in March 2020, rose to ₹55.00 by August 2023, and has declined since. "
            "Past movements do not predict future returns. This view is about the fund only."
        ),
        "patterns": [
            {
                "type": "rally",
                "title": "+90.9% in 20 months",
                "subtitle": "Mar'20 to Nov'21, ₹22.00 to ₹42.00",
                "note": "Market prices moved up and down during this period.",
            },
            {
                "type": "correction",
                "title": "-33.3% in 16 months",
                "subtitle": "Nov'18 to Mar'20, ₹33.00 to ₹22.00",
                "note": "Market prices moved up and down during this period.",
            },
        ],
        "stats": {
            "start_nav": "₹33.00",
            "start_nav_sub": "Nov '18 baseline",
            "current_nav": "₹44.75",
            "current_nav_sub": "November cut-off",
            "period_return": "+35.61%",
            "period_return_sub": "about 6.3% a year",
            "max_drawdown": "-33.3%",
            "max_drawdown_sub": "Peak to trough",
            "benchmark": "+48.0%",
            "benchmark_sub": "Nifty 50 (sample)",
            "risk_category": "Very High",
            "risk_sub": "SEBI Standard",
        },
    },
}

# Navy Quiz card data on Fund History
FUND_HISTORY_QUIZ = {
    "question": "A fund's NAV is down about 8% since you started, but your SIP is down about 12%. Why can this happen?",
    "options": [
        "The fund charged a hidden penalty",
        "Most of your instalments were bought at higher NAVs than the starting NAV",
        "SIP returns are always lower than fund returns",
    ],
    "correct_index": 1,
    "explanation": "Your SIP bought units at 7 different prices, mostly higher than the starting NAV, so its return can differ from the fund's.",
}

# Educational Graph Reading FAQs
LEARN_GRAPH_ITEMS = [
    {
        "q": "What is NAV?",
        "a": "Net Asset Value is the combined market value of the fund's holdings minus liabilities, divided by total outstanding units. It represents per-unit intrinsic book value.",
    },
    {
        "q": "Does a falling NAV graph mean the fund is failing?",
        "a": "No. Markets fluctuate regularly due to economic cycles. A lower NAV lets your fixed monthly SIP buy more units, but it does not guarantee prices will recover.",
    },
]

# Educational takeaways on Fund History
FUND_HISTORY_TAKEAWAYS = [
    "Fund NAV dropped -7.73% while your SIP dropped -12.14% due to higher mid-cycle acquisition prices.",
    "Rally and drawdown periods affect lumpsum returns differently than recurring monthly SIP purchases.",
    "Key Rule: Historical performance is useful for understanding past fund behaviour, but it does NOT guarantee future returns.",
]

