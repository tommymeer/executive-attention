"""
convergence.py
Executive Attention Synthesizer — Convergence Engine

Theme aggregation, convergence scoring, output classification,
and signal bundle construction. Fully deterministic. No Claude.

Scoring formula:
    theme_score = distinct_tool_count × max_severity × signal_count_modifier

Business context does NOT affect scores. It affects output ranking only.
"""

from theme_config import CANONICAL_THEMES, THEME_LABELS, THEME_RANK


# ── Score thresholds ──────────────────────────────────────────────────────────

CONVERGENT_THRESHOLD = 6.0
WATCH_THRESHOLD = 3.0

# ── Signal count modifier ─────────────────────────────────────────────────────

def signal_count_modifier(n: int) -> float:
    if n == 1:
        return 1.0
    elif n == 2:
        return 1.2
    else:
        return 1.5


# ── Theme aggregation ─────────────────────────────────────────────────────────

def aggregate_by_theme(signals: list) -> dict:
    """
    Groups signals by canonical theme.
    Returns dict: {theme: [signal, ...]}
    """
    theme_map = {theme: [] for theme in CANONICAL_THEMES}
    for signal in signals:
        for theme in signal.get("themes", []):
            if theme in theme_map:
                theme_map[theme].append(signal)
    return theme_map


# ── Convergence scoring ───────────────────────────────────────────────────────

def score_theme(theme_signals: list) -> dict:
    """
    Computes convergence score for a single theme's signal list.
    Returns scoring breakdown dict.
    """
    if not theme_signals:
        return {"score": 0.0, "distinct_tool_count": 0,
                "max_severity": 0, "signal_count": 0, "modifier": 1.0}

    distinct_tools = list({s["source_tool"] for s in theme_signals})
    distinct_tool_count = len(distinct_tools)
    max_severity = max(s["severity"] for s in theme_signals)
    signal_count = len(theme_signals)
    modifier = signal_count_modifier(signal_count)

    score = distinct_tool_count * max_severity * modifier

    return {
        "score": round(score, 2),
        "distinct_tool_count": distinct_tool_count,
        "distinct_tools": distinct_tools,
        "max_severity": max_severity,
        "signal_count": signal_count,
        "modifier": modifier,
    }


def score_all_themes(theme_map: dict) -> dict:
    """
    Scores all themes. Returns dict: {theme: scoring_breakdown}
    """
    return {theme: score_theme(signals)
            for theme, signals in theme_map.items()}


# ── Time pressure detection ───────────────────────────────────────────────────

_URGENCY_TERMS = [
    "this week", "next week", "monday", "tuesday", "wednesday",
    "thursday", "friday", "eow", "eom", "eoq", "days",
    "june", "july", "august", "deadline", "before", "by ",
    "end of", "close", "q3", "q4",
]

def has_time_pressure(theme_signals: list) -> tuple:
    """
    Returns (bool, str) — whether any signal has a near-term time reference,
    and the first one found.
    """
    for signal in theme_signals:
        ref = signal.get("week_reference", "")
        text = signal.get("text", "").lower()
        if ref:
            return True, ref
        for term in _URGENCY_TERMS:
            if term in text:
                # Extract snippet around the term
                idx = text.find(term)
                snippet = text[max(0, idx-10):idx+30].strip()
                return True, snippet
    return False, ""


# ── Output classification ─────────────────────────────────────────────────────

def classify_findings(theme_map: dict, scores: dict) -> dict:
    """
    Routes convergent themes to output buckets.

    Returns:
        {
            "requires_attention": [...],
            "cannot_postpone": [...],
            "watch": [...],
        }
    Each item is a dict with theme, score breakdown, signals, and time_reference.
    """
    requires_attention = []
    cannot_postpone = []
    watch = []

    for theme, score_info in scores.items():
        score = score_info["score"]
        distinct_tool_count = score_info["distinct_tool_count"]
        theme_signals = theme_map[theme]

        if score <= 0:
            continue

        item = {
            "theme": theme,
            "theme_label": THEME_LABELS[theme],
            "score": score,
            "score_info": score_info,
            "signals": theme_signals,
            "time_reference": "",
        }

        if score >= CONVERGENT_THRESHOLD and distinct_tool_count >= 2:
            # All convergent findings go into requires_attention
            requires_attention.append(item)

            # Check for time pressure → also goes into cannot_postpone
            has_pressure, time_ref = has_time_pressure(theme_signals)
            item["time_reference"] = time_ref
            if has_pressure:
                cannot_postpone.append(item)

        elif score >= WATCH_THRESHOLD:
            watch.append(item)

    # Sort each bucket by score descending
    requires_attention.sort(key=lambda x: x["score"], reverse=True)
    cannot_postpone.sort(key=lambda x: x["score"], reverse=True)
    watch.sort(key=lambda x: x["score"], reverse=True)

    return {
        "requires_attention": requires_attention,
        "cannot_postpone": cannot_postpone,
        "watch": watch,
    }


# ── Company-type ranking ──────────────────────────────────────────────────────

def apply_company_type_ranking(findings: dict, company_type: str) -> dict:
    """
    Reorders findings within Requires Attention bucket based on company type.
    Scores are unchanged. Only display order changes.
    """
    rank_order = THEME_RANK.get(company_type, [])
    if not rank_order:
        return findings  # "Other" — keep raw score order

    def rank_key(item):
        theme = item["theme"]
        try:
            return rank_order.index(theme)
        except ValueError:
            return len(rank_order)  # unranked themes go to end

    findings["requires_attention"] = sorted(
        findings["requires_attention"],
        key=lambda x: (rank_key(x), -x["score"])
    )
    return findings


# ── Signal bundle construction ────────────────────────────────────────────────

def build_signal_bundles(findings: dict, business_context: dict) -> dict:
    """
    Packages each classified finding into a structured bundle
    for the Claude reasoning layer.

    Returns dict with same structure as findings but with bundle field added.
    """
    company_type = business_context.get("company_type", "Other")
    stage = business_context.get("stage", "")
    optional_context = business_context.get("optional_context", "")

    def build_bundle(item: dict, classification: str) -> str:
        score_info = item["score_info"]
        signals = item["signals"]

        lines = [
            f"CONVERGENT THEME: {item['theme_label']} ({item['theme']})",
            f"Theme Score: {item['score']}",
            f"Distinct Tools: {score_info['distinct_tool_count']} "
            f"({', '.join(score_info['distinct_tools'])})",
            f"Classification: {classification}",
            "",
            "Contributing Signals:",
        ]

        for s in signals:
            lines.append(
                f"  - [{s['source_tool']}, Severity {s['severity']}] \"{s['text']}\""
            )
            if s.get("week_reference"):
                lines.append(f"    Time reference: {s['week_reference']}")

        if item.get("time_reference"):
            lines.append(f"\nTime pressure: {item['time_reference']}")

        badge_tools = sorted(set(s["source_tool"] for s in signals))
        lines.append(f"Badge Sources: {' | '.join(badge_tools)}")

        lines.append("")
        lines.append(f"Business Context: {company_type} — {stage}")
        if optional_context:
            lines.append(f"Optional Context: {optional_context}")

        return "\n".join(lines)

    # Build bundles for requires_attention
    for item in findings["requires_attention"]:
        item["bundle"] = build_bundle(item, "Requires Attention Now")

    # Build bundles for cannot_postpone
    for item in findings["cannot_postpone"]:
        item["bundle"] = build_bundle(item, "Decision Cannot Be Postponed")

    # Top 2 convergent themes for What the Signals Suggest
    all_convergent = sorted(
        findings["requires_attention"] + findings["cannot_postpone"],
        key=lambda x: x["score"],
        reverse=True,
    )
    findings["top_for_observation"] = all_convergent[:2]

    return findings


# ── Master convergence runner ─────────────────────────────────────────────────

def run_convergence(signals: list, business_context: dict) -> dict:
    """
    Main entry point. Takes extracted signals and business context.
    Returns fully classified and bundled findings.
    """
    theme_map = aggregate_by_theme(signals)
    scores = score_all_themes(theme_map)
    findings = classify_findings(theme_map, scores)
    findings = apply_company_type_ranking(
        findings, business_context.get("company_type", "Other")
    )
    findings = build_signal_bundles(findings, business_context)

    # Attach full scores for Watch Items display
    findings["all_scores"] = scores
    findings["theme_map"] = theme_map

    return findings
