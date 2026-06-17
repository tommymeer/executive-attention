"""
signal_extraction.py
Executive Attention Synthesizer — Signal Extraction Layer

Parses each tool output (.txt) into structured signal objects.
Deterministic. No Claude. Regex and pattern matching only.
"""

import re
from typing import Optional
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
    # Cap at 3 themes per signal
    return matched[:3] if matched else []


# ── Line extraction utilities ─────────────────────────────────────────────────

def extract_relevant_lines(text: str, section_markers: list,
                           min_length: int = 20) -> list:
    """
    Extracts lines from sections whose headers match section_markers.
    Returns list of non-empty lines from those sections.
    """
    lines = text.split("\n")
    relevant = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Check if this line is a section header
        is_header = any(marker in lower for marker in section_markers)
        if is_header and len(stripped) < 80:
            in_section = True
            continue

        # Check if we've hit a new major section (uppercase header, dashes, etc.)
        if in_section and stripped and (
            re.match(r"^#{1,3}\s", stripped) or
            re.match(r"^[A-Z][A-Z\s]{4,}$", stripped) or
            re.match(r"^[-=]{3,}$", stripped)
        ):
            # Only exit section if it's clearly a new top-level section
            # and not a bullet continuation
            if not stripped.startswith("-") and not stripped.startswith("•"):
                in_section = False

        if in_section and len(stripped) >= min_length:
            relevant.append(stripped)

    # Fallback: if no section headers matched, extract all substantive lines
    if not relevant:
        for line in lines:
            stripped = line.strip()
            if len(stripped) >= min_length and not re.match(r"^#{1,3}\s", stripped):
                relevant.append(stripped)

    return relevant


def split_into_sentences(text: str) -> list:
    """Split text into sentence-like chunks for signal extraction."""
    # Split on sentence endings and bullet points
    chunks = re.split(r'(?<=[.!?])\s+|(?=\n[-•·])', text)
    return [c.strip() for c in chunks if len(c.strip()) >= 20]


# ── Per-tool extraction ───────────────────────────────────────────────────────

def extract_from_wbr(text: str, tool_index: int) -> list:
    """Extract signals from WBR Generator output."""
    signals = []
    lines = extract_relevant_lines(text, WBR_EXTRACT_SECTIONS)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)
        time_ref = extract_time_reference(line)

        # Determine signal type
        signal_type = "Risk"
        if any(w in line.lower() for w in ["decision", "requires", "action"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["anomal", "unexpected", "unusual"]):
            signal_type = "Anomaly"
        elif any(w in line.lower() for w in ["decline", "drop", "below", "miss"]):
            signal_type = "Risk"

        signal = make_signal(
            signal_id=f"wbr_{tool_index}_{i}",
            source_tool="WBR",
            domain="Performance",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        )
        signals.append(signal)

    return signals


def extract_from_meeting(text: str, tool_index: int) -> list:
    """Extract signals from Meeting Intelligence output."""
    signals = []
    lines = extract_relevant_lines(text, MEETING_EXTRACT_SECTIONS)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        base_severity = score_severity(line)
        severity = boost_deferral_severity(line, base_severity)
        time_ref = extract_time_reference(line)

        # Determine signal type
        signal_type = "Deferral"
        if any(w in line.lower() for w in ["blocker", "blocked", "impediment"]):
            signal_type = "Block"
        elif any(w in line.lower() for w in ["decision", "decided", "agreed"]):
            signal_type = "Gap"
        elif any(w in line.lower() for w in ["open", "unresolved", "pending", "tbd"]):
            signal_type = "Deferral"

        signal = make_signal(
            signal_id=f"meeting_{tool_index}_{i}",
            source_tool="Meeting",
            domain="Decision",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        )
        signals.append(signal)

    return signals


def extract_from_pipeline(text: str, tool_index: int) -> list:
    """Extract signals from Pipeline Synthesizer output."""
    signals = []
    lines = extract_relevant_lines(text, PIPELINE_EXTRACT_SECTIONS)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)

        # Pipeline-specific severity boost: named deals + inactivity
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

        signal = make_signal(
            signal_id=f"pipeline_{tool_index}_{i}",
            source_tool="Pipeline",
            domain="Commercial",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        )
        signals.append(signal)

    return signals


def extract_from_initiative(text: str, tool_index: int) -> list:
    """Extract signals from Initiative Intelligence output."""
    signals = []
    lines = extract_relevant_lines(text, INITIATIVE_EXTRACT_SECTIONS)

    for i, line in enumerate(lines):
        themes = map_themes(line)
        if not themes:
            continue

        severity = score_severity(line)

        # Initiative severity override: blocked + strategic bet = severity 3
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

        signal = make_signal(
            signal_id=f"initiative_{tool_index}_{i}",
            source_tool="Initiative",
            domain="Strategic",
            signal_type=signal_type,
            severity=severity,
            themes=themes,
            text=line[:300],
            week_reference=time_ref,
        )
        signals.append(signal)

    return signals


# ── Master extraction dispatcher ──────────────────────────────────────────────

def extract_signals(tool_outputs: dict) -> list:
    """
    Main entry point. Accepts dict of {tool_name: text_content}.
    Returns combined list of signal objects across all provided tools.

    tool_outputs keys: "WBR", "Meeting", "Pipeline", "Initiative"
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
    """Returns a summary of what was extracted for debugging and coverage header."""
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
        }
    }
