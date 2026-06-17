"""
components/output_display.py
Executive Attention Synthesizer — Output Display Component

Renders coverage header, all three output sections, and Watch Items.
Badge attribution is deterministic — sourced from signal bundles, not Claude.
"""

import streamlit as st


# ── Coverage header ───────────────────────────────────────────────────────────

def render_coverage_header(tool_outputs: dict):
    """Four domain badges showing which organizational realities are present."""
    domains = {
        "WBR":        ("Performance", "🟢", "⚪"),
        "Meeting":    ("Decision", "🟢", "⚪"),
        "Pipeline":   ("Commercial", "🟢", "⚪"),
        "Initiative": ("Strategic", "🟢", "⚪"),
    }

    cols = st.columns(4)
    for i, (tool, (domain, active_icon, inactive_icon)) in enumerate(domains.items()):
        with cols[i]:
            is_present = tool in tool_outputs
            icon = active_icon if is_present else inactive_icon
            status = "Present" if is_present else "Not provided"
            color = "#2d6a4f" if is_present else "#888888"
            st.markdown(
                f"""<div style='text-align:center; padding:12px; 
                    border:1px solid {"#2d6a4f" if is_present else "#dddddd"}; 
                    border-radius:6px; background:{"#d8f3dc" if is_present else "#f8f8f8"}'>
                    <div style='font-size:20px'>{icon}</div>
                    <div style='font-weight:600; color:{color}; font-size:13px'>{domain}</div>
                    <div style='font-size:11px; color:#888'>{tool}</div>
                    <div style='font-size:11px; color:{color}'>{status}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    missing = [tool for tool in domains if tool not in tool_outputs]
    if missing:
        missing_domains = [domains[t][0] for t in missing]
        st.caption(
            f"⚠ {', '.join(missing_domains)} signal(s) not provided. "
            f"Convergence analysis reflects available domains only. "
            f"Cross-domain findings may be understated."
        )


# ── Badge renderer ────────────────────────────────────────────────────────────

TOOL_COLORS = {
    "WBR":        ("#1b4332", "#d8f3dc"),
    "Meeting":    ("#1c3a5e", "#dbeafe"),
    "Pipeline":   ("#5c2d0e", "#fde8d0"),
    "Initiative": ("#3b1f5e", "#ede9fe"),
}

def render_badges(badge_sources: list):
    badge_html = ""
    for source in badge_sources:
        fg, bg = TOOL_COLORS.get(source, ("#333", "#eee"))
        badge_html += (
            f"<span style='background:{bg}; color:{fg}; "
            f"padding:3px 10px; border-radius:12px; font-size:11px; "
            f"font-weight:600; margin-right:6px'>{source}</span>"
        )
    st.markdown(badge_html, unsafe_allow_html=True)


# ── Requires Attention Now ────────────────────────────────────────────────────

def escape_dollars(text: str) -> str:
    """Escape dollar signs to prevent Streamlit from rendering them as LaTeX."""
    return text.replace("$", r"\$")


def render_attention_findings(attention_findings: list):
    if not attention_findings:
        st.info("No convergent themes detected above threshold in the provided signals.")
        return

    for finding in attention_findings:
        with st.container():
            st.markdown(
                f"<h4 style='margin-bottom:4px'>▸ {finding['theme_label']}</h4>",
                unsafe_allow_html=True,
            )
            render_badges(finding.get("badge_sources", []))
            st.markdown("")
            st.markdown(escape_dollars(finding.get("synthesis", "")))
            st.markdown(
                f"**Required action:** {escape_dollars(finding.get('required_action', ''))}",
            )
            st.markdown("---")


# ── Decision Cannot Be Postponed ──────────────────────────────────────────────

def render_decision_findings(decision_findings: list):
    if not decision_findings:
        return

    for finding in decision_findings:
        with st.container():
            st.markdown(
                f"<h4 style='margin-bottom:4px; color:#b91c1c'>⚑ {finding['theme_label']}</h4>",
                unsafe_allow_html=True,
            )
            render_badges(finding.get("badge_sources", []))
            st.markdown("")
            st.markdown(escape_dollars(finding.get("synthesis", "")))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Decision required:** {escape_dollars(finding.get('decision_required', ''))}")
            with col2:
                if finding.get("deadline_reference"):
                    st.markdown(f"**Deadline:** {escape_dollars(finding.get('deadline_reference', ''))}")

            if finding.get("consequence_of_deferral"):
                st.markdown(
                    f"<div style='background:#fef2f2; padding:10px; border-left:3px solid #b91c1c; "
                    f"border-radius:4px; font-size:13px; color:#7f1d1d; margin-top:8px'>"
                    f"⚠ {escape_dollars(finding['consequence_of_deferral'])}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")


# ── What the Signals Suggest ──────────────────────────────────────────────────

def render_signal_observation(signal_observation: dict):
    if not signal_observation:
        return

    st.markdown(
        "<div style='background:#fafafa; border:1px solid #e5e7eb; "
        "border-radius:8px; padding:20px; margin-top:8px'>",
        unsafe_allow_html=True,
    )

    st.markdown("**Observed Pattern**")
    st.markdown(signal_observation.get("observed_pattern", ""))
    st.markdown("")

    st.markdown("**Likely Implicit Belief**")
    st.markdown(
        f"<div style='color:#374151; font-style:italic'>"
        f"{signal_observation.get('likely_implicit_belief', '')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    st.markdown("**Alternative Explanation**")
    st.markdown(
        f"<div style='background:#eff6ff; padding:12px; border-radius:6px; "
        f"border-left:3px solid #3b82f6; font-size:13px'>"
        f"{signal_observation.get('alternative_explanation', '')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Watch Items ───────────────────────────────────────────────────────────────

def render_watch_items(watch_items: list):
    if not watch_items:
        return

    with st.expander(f"Watch Items ({len(watch_items)} emerging patterns — below convergence threshold)"):
        st.caption(
            "These themes have signal but do not yet meet the convergence threshold "
            "(score ≥ 6, distinct tools ≥ 2). Scores are shown for reference."
        )
        for item in watch_items:
            si = item["score_info"]
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.markdown(f"**{item['theme_label']}**")
            with col2:
                st.markdown(f"Score: **{item['score']}**")
            with col3:
                tool_str = " · ".join(si.get("distinct_tools", []))
                st.caption(f"{tool_str} · severity {si['max_severity']}")


# ── Master output renderer ────────────────────────────────────────────────────

def render_full_output(reasoning_output: dict, findings: dict, tool_outputs: dict):
    """Main entry point. Renders all output sections in order."""

    # Coverage header
    st.subheader("Signal Coverage")
    render_coverage_header(tool_outputs)
    st.markdown("")

    # Requires Attention Now
    st.subheader("Requires Attention Now")
    render_attention_findings(reasoning_output.get("attention_findings", []))

    # Decision Cannot Be Postponed
    decision_findings = reasoning_output.get("decision_findings", [])
    if decision_findings:
        st.subheader("Decision Cannot Be Postponed")
        render_decision_findings(decision_findings)

    # What the Signals Suggest
    observation = reasoning_output.get("signal_observation")
    if observation:
        st.subheader("What the Signals Suggest")
        render_signal_observation(observation)
        st.markdown("")

    # Watch Items
    watch = findings.get("watch", [])
    if watch:
        render_watch_items(watch)
