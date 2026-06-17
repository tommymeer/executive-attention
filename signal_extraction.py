"""
signal_extraction.py
Executive Attention Synthesizer — Signal Extraction Layer

Parses each tool output (.txt) into structured signal objects.
Deterministic. No Claude. Regex and pattern matching only.

Changes from v1:
- Removed full-document fallback in extract_relevant_lines.
  If no section headers match, return empty list with a warning flag.
  Prevents keyword matching from firing on every line of every output.
- Added per-tool signal cap (MAX_SIGNALS_PER_TOOL = 20).
  Prevents high-volume tools from dominating convergence scores.
- Signals sorted by severity before cap is applied — highest quality first.
"""

import re
from theme_config import (
    THEME_KEYWORDS,
    SEVERITY_3_MARKERS,
    SEVERITY_2_MARKERS,
    WBR_EXTRACT_SECTIONS,
    MEETING_EXTRACT_SECTIONS,
    PIPELINE_EXTRACT_SECTIONS,
    INITIATIVE_EXTRACT_SECTIONS,
    DEFERRAL_MARKERS,
    TIME_REFERENCE_PATTERNS,
)

# Maximum signals extracted per tool per run.
# Prevents dense outputs from inflating convergence scores.
# Signals are sorted by severity before cap — highest severity signals kept.
MAX_SIGNALS_PER_TOOL = 20


# ── Signal object ─────────────────────────────────────────────────────────────

def make_signal(signal_id: str, source_tool: str, domain: str,
                signal_type: str, severity: int, themes: list,
                text: str, week_reference: str = "") -> dict:
    return {
        "signal_id": signal_id,
        "source_tool": source_tool,
        "domain": domain,
        "signal_type": signal_type,
        "severity": severity,
        "themes": themes,
        "text": text,
        "week_reference": week_reference,
    }


# ── Severity scoring ──────────────────────────────────────────────────────────

def score_severity(text: str) -> int:
    lower = text.lower()
    for marker in SEVERITY_3_MARKERS:
        if marker in lower:
            return 3
    for marker in SEVERITY_2_MARKERS:
        if marker in lower:
            return 2
    return 1


def boost_deferral_severity(text: str, base_severity: int) -> int:
    """Meeting Intelligence: recurring deferrals are severity 3 regardless."""
    lower = text.lower()
    for marker in DEFERRAL_MARKERS:
        if marker in lower:
            return 3
    return base_severity


# ── Time reference extraction ─────────────────────────────────────────────────

def extract_time_reference(text: str) -> str:
    lower = text.lower()
    for pattern in TIME_REFERENCE_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            return match.group(0).strip()
    return ""


# ── Theme mapping ─────────────────────────────────────────────────────────────

def map_themes(text: str) -> list:
    lower = text.lower()
    matched = []
    for theme, keywords in THEME_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                matched.append(theme)
                break
    return matched[:3] if matched else []


# ── Line extraction — section-header gated ────────────────────────────────────

def extract_relevant_lines(text: str, section_markers: list,
                           min_length: int = 20) -> tuple:
    """
    Extracts lines from sections whose headers match section_markers.
    Returns (lines, matched_sections_count).

    A line is treated as a section header only if it BOTH:
    1. Contains a section marker keyword
    2. Looks structurally like a header

    Header patterns recognized:
    - ## Markdown headers
    - ALL CAPS headers
    - Roman numeral prefixed: "III. Anomalies & Risks"
    - Numbered: "1. Header"
    - Title case, short, no sentence punctuation: "Drift Findings"
    - Short label ending with colon: "Risks:"

    This prevents content lines that happen to contain keywords from
    being misidentified as section headers.
    """
    lines = text.split("\n")
    relevant = []
    in_section = False
    matched_sections = 0

    def looks_like_header(stripped):
        return (
            bool(re.match(r"^#{1,3}\s", stripped)) or
            bool(re.match(r"^[A-Z][A-Z\s&/]{3,}$", stripped)) or
            (len(stripped) < 50 and stripped.endswith(":")) or
            bool(re.match(r"^[IVXivx]+\.\s+[A-Z]", stripped)) or
            bool(re.match(r"^\d+\.\s+[A-Z]", stripped)) or
            (len(stripped) < 60 and
             bool(re.match(r"^[A-Z][a-zA-Z\s&/–-]+$", stripped)) and
             not stripped.endswith(".") and
             not stripped.endswith(",") and
             stripped.count(" ") <= 5)
        )

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        contains_marker = any(marker in lower for marker in section_markers)
        is_header = contains_marker and looks_like_header(stripped)

        if is_header:
            in_section = True
            matched_sections += 1
            continue

        # Exit section on any new top-level header structure
        if in_section and stripped and (
            re.match(r"^#{1,3}\s", stripped) or
            re.match(r"^[A-Z][A-Z\s]{4,}$", stripped) or
            re.match(r"^[-=]{3,}$", stripped) or
            (looks_like_header(stripped) and not stripped.startswith("-") and
             not stripped.startswith("•"))
        ):
            in_section = False

        if in_section and len(stripped) >= min_length:
            relevant.append(stripped)

    return relevant, matched_sections

def apply_signal_cap(signals: list, cap: int = MAX_SIGNALS_PER_TOOL) -> list:
    """
    Sort signals by severity descending, then apply cap.
    Highest-severity signals are kept when cap is applied.
    """
    sorted_signals = sorted(signals, key=lambda s: s["severity"], reverse=True)
    return sorted_signals[:cap]


# ── Per-tool extraction ───────────────────────────────────────────────────────

def extract_from_wbr(text: str, tool_index: int) -> list:
    """Extract signals from WBR Generator output."""
    signals = []
    lines, matched = extract_relevant_lines(text, WBR_EXTRACT_SECTIONS)

    if matched == 0:
        # No recognized section headers — extract conservatively from
        # lines that contain both a severity marker AND a theme keyword.
        # This is a tighter constraint than full-document fallback.
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) < 20:
                continue
            lower = stripped.lower()
            has_severity = any(m in lower for m in SEVERITY_3_MARKERS + SEVERITY_2_MARKERS)
            if not has_severity:
                continue
            themes = map_themes(stripped)
            if themes:
                lines.append(stripped)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)
        time_ref = extract_time_reference(line)

        signal_type = "Risk"
        if any(w in line.lower() for w in ["decision", "requires", "action"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["anomal", "unexpected", "unusual"]):
            signal_type = "Anomaly"
        elif any(w in line.lower() for w in ["decline", "drop", "below", "miss"]):
            signal_type = "Risk"

        signals.append(make_signal(
            signal_id=f"wbr_{tool_index}_{i}",
            source_tool="WBR",
            domain="Performance",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        ))

    return apply_signal_cap(signals)


def extract_from_meeting(text: str, tool_index: int) -> list:
    """Extract signals from Meeting Intelligence output."""
    signals = []
    lines, matched = extract_relevant_lines(text, MEETING_EXTRACT_SECTIONS)

    if matched == 0:
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) < 20:
                continue
            lower = stripped.lower()
            has_severity = any(m in lower for m in SEVERITY_3_MARKERS + SEVERITY_2_MARKERS + DEFERRAL_MARKERS)
            if not has_severity:
                continue
            themes = map_themes(stripped)
            if themes:
                lines.append(stripped)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        base_severity = score_severity(line)
        severity = boost_deferral_severity(line, base_severity)
        time_ref = extract_time_reference(line)

        signal_type = "Deferral"
        if any(w in line.lower() for w in ["blocker", "blocked", "impediment"]):
            signal_type = "Block"
        elif any(w in line.lower() for w in ["decision", "decided", "agreed"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["open", "unresolved", "pending", "tbd"]):
            signal_type = "Deferral"

        signals.append(make_signal(
            signal_id=f"meeting_{tool_index}_{i}",
            source_tool="Meeting",
            domain="Decision",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        ))

    return apply_signal_cap(signals)


def extract_from_pipeline(text: str, tool_index: int) -> list:
    """Extract signals from Pipeline Synthesizer output."""
    signals = []
    lines, matched = extract_relevant_lines(text, PIPELINE_EXTRACT_SECTIONS)

    if matched == 0:
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) < 20:
                continue
            lower = stripped.lower()
            has_severity = any(m in lower for m in SEVERITY_3_MARKERS + SEVERITY_2_MARKERS)
            if not has_severity:
                continue
            themes = map_themes(stripped)
            if themes:
                lines.append(stripped)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)

        if (any(w in line.lower() for w in ["negotiation", "proposal", "late stage"])
                and any(w in line.lower() for w in ["no activity", "stall", "14", "days"])):
            severity = 3

        time_ref = extract_time_reference(line)

        signal_type = "Risk"
        if any(w in line.lower() for w in ["gap", "coverage", "thin"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["stall", "no activity", "stuck"]):
            signal_type = "Block"
        elif any(w in line.lower() for w in ["action", "leadership"]):
            signal_type = "Gap"

        signals.append(make_signal(
            signal_id=f"pipeline_{tool_index}_{i}",
            source_tool="Pipeline",
            domain="Commercial",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        ))

    return apply_signal_cap(signals)


def extract_from_initiative(text: str, tool_index: int) -> list:
    """Extract signals from Initiative Intelligence output."""
    signals = []
    lines, matched = extract_relevant_lines(text, INITIATIVE_EXTRACT_SECTIONS)

    if matched == 0:
        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) < 20:
                continue
            lower = stripped.lower()
            has_severity = any(m in lower for m in SEVERITY_3_MARKERS + SEVERITY_2_MARKERS)
            if not has_severity:
                continue
            themes = map_themes(stripped)
            if themes:
                lines.append(stripped)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)

        if (any(w in line.lower() for w in ["blocked", "blocker"])
                and any(w in line.lower() for w in ["strategic", "bet", "priority"])):
            severity = 3

        time_ref = extract_time_reference(line)

        signal_type = "Risk"
        if any(w in line.lower() for w in ["blocked", "blocker"]):
            signal_type = "Block"
        elif any(w in line.lower() for w in ["drift", "misalign", "off-strategy"]):
            signal_type = "Anomaly"
        elif any(w in line.lower() for w in ["gap", "missing", "absent", "no initiative"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["delay", "behind", "slipping"]):
            signal_type = "Risk"

        signals.append(make_signal(
            signal_id=f"initiative_{tool_index}_{i}",
            source_tool="Initiative",
            domain="Strategic",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        ))

    return apply_signal_cap(signals)


# ── Master extraction dispatcher ──────────────────────────────────────────────

def extract_signals(tool_outputs: dict) -> list:
    """
    Main entry point. Accepts dict of {tool_name: text_content}.
    Returns combined list of signal objects across all provided tools.
    Each tool contributes at most MAX_SIGNALS_PER_TOOL signals.
    """
    all_signals = []
    extractors = {
        "WBR": extract_from_wbr,
        "Meeting": extract_from_meeting,
        "Pipeline": extract_from_pipeline,
        "Initiative": extract_from_initiative,
    }

    for tool_index, (tool_name, text) in enumerate(tool_outputs.items()):
        if text and tool_name in extractors:
            tool_signals = extractors[tool_name](text, tool_index)
            all_signals.extend(tool_signals)

    return all_signals


# ── Signal quality summary ────────────────────────────────────────────────────

def summarize_extraction(signals: list, tool_outputs: dict) -> dict:
    tool_counts = {}
    for tool in tool_outputs:
        tool_counts[tool] = len([s for s in signals if s["source_tool"] == tool])

    return {
        "total_signals": len(signals),
        "by_tool": tool_counts,
        "tools_present": list(tool_outputs.keys()),
        "has_time_references": len([s for s in signals if s["week_reference"]]),
        "severity_distribution": {
            1: len([s for s in signals if s["severity"] == 1]),
            2: len([s for s in signals if s["severity"] == 2]),
            3: len([s for s in signals if s["severity"] == 3]),
        },
        "cap_applied": MAX_SIGNALS_PER_TOOL,
    }
