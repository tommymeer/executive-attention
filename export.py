"""
export.py
Executive Attention Synthesizer — Export Builder

Assembles the .txt download from all output sections.
Includes business context, coverage summary, scores, and all findings.
"""

from datetime import datetime


def build_export(business_context: dict, tool_outputs: dict,
                 findings: dict, reasoning_output: dict) -> str:
    lines = []

    # Header
    lines += [
        "EXECUTIVE ATTENTION SYNTHESIZER",
        "Ground Truth Decisioning System · thomasmeerschwam.com",
        f"Generated: {datetime.now().strftime('%B %d, %Y · %I:%M %p')}",
        "=" * 60,
        "",
    ]

    # Business context
    lines += [
        "BUSINESS CONTEXT",
        f"Company Type: {business_context.get('company_type', 'Not specified')}",
        f"Stage: {business_context.get('stage', 'Not specified')}",
    ]
    if business_context.get("optional_context"):
        lines.append(f"Additional Context: {business_context['optional_context']}")
    lines.append("")

    # Coverage summary
    lines += ["SIGNAL COVERAGE"]
    domain_map = {
        "WBR": "Performance",
        "Meeting": "Decision",
        "Pipeline": "Commercial",
        "Initiative": "Strategic",
    }
    for tool, domain in domain_map.items():
        status = "✓ Present" if tool in tool_outputs else "— Not provided"
        lines.append(f"  {domain} ({tool}): {status}")
    lines.append("")

    # Requires Attention Now
    attention = reasoning_output.get("attention_findings", [])
    if attention:
        lines += ["=" * 60, "REQUIRES ATTENTION NOW", "=" * 60, ""]
        for finding in attention:
            lines += [
                f"▸ {finding['theme_label']}",
                "",
                finding.get("synthesis", ""),
                "",
                f"Required action: {finding.get('required_action', '')}",
                "",
                f"Sources: {' · '.join(finding.get('badge_sources', []))}",
                "",
                "—" * 40,
                "",
            ]

    # Decision Cannot Be Postponed
    decisions = reasoning_output.get("decision_findings", [])
    if decisions:
        lines += ["=" * 60, "DECISION CANNOT BE POSTPONED", "=" * 60, ""]
        for finding in decisions:
            lines += [
                f"▸ {finding['theme_label']}",
                "",
                finding.get("synthesis", ""),
                "",
                f"Decision required: {finding.get('decision_required', '')}",
                f"Deadline: {finding.get('deadline_reference', '')}",
                f"Cost of deferral: {finding.get('consequence_of_deferral', '')}",
                "",
                f"Sources: {' · '.join(finding.get('badge_sources', []))}",
                "",
                "—" * 40,
                "",
            ]

    # What the Signals Suggest
    observation = reasoning_output.get("signal_observation")
    if observation:
        lines += ["=" * 60, "WHAT THE SIGNALS SUGGEST", "=" * 60, ""]
        lines += [
            "Primary Hypothesis:",
            observation.get("primary_hypothesis", ""),
            "",
            "Competing Hypothesis:",
            observation.get("competing_hypothesis", ""),
            "",
            "Unresolved Ambiguity:",
            observation.get("unresolved_ambiguity", ""),
            "",
        ]

    # Watch Items (from deterministic layer)
    watch = findings.get("watch", [])
    if watch:
        lines += ["=" * 60, "WATCH ITEMS", "(Emerging signals — below convergence threshold)", "=" * 60, ""]
        for item in watch:
            si = item["score_info"]
            lines.append(
                f"  {item['theme_label']}: score {item['score']} · "
                f"{si['distinct_tool_count']} tool(s) · "
                f"max severity {si['max_severity']} · "
                f"{si['signal_count']} signal(s)"
            )
        lines.append("")

    # Theme scores (full, for reference)
    lines += ["=" * 60, "CONVERGENCE SCORES (All Themes)", "=" * 60]
    all_scores = findings.get("all_scores", {})
    sorted_themes = sorted(all_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    for theme, score_info in sorted_themes:
        if score_info["score"] > 0:
            from theme_config import THEME_LABELS
            label = THEME_LABELS.get(theme, theme)
            lines.append(
                f"  {label}: {score_info['score']} "
                f"(tools: {score_info['distinct_tool_count']}, "
                f"severity: {score_info['max_severity']}, "
                f"signals: {score_info['signal_count']})"
            )
    lines.append("")

    lines += [
        "=" * 60,
        "Executive Attention Synthesizer · Ground Truth Decisioning System",
        "thomasmeerschwam.com",
    ]

    return "\n".join(lines)
