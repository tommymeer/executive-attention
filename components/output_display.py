"""
components/output_display.py
Executive Attention Synthesizer — Output Display Component

Cards are created from deterministic bundles.
Claude fills narrative text. Fallback text renders if Claude fails.
Sections always exist. Claude never decides whether a section appears.
"""

import streamlit as st


# ── Utility ───────────────────────────────────────────────────────────────────

def escape_dollars(text: str) -> str:
    """Prevent Streamlit from rendering dollar signs as LaTeX."""
    return text.replace("$", r"\$")


# ── Coverage header ───────────────────────────────────────────────────────────

def render_coverage_header(tool_outputs: dict):
    domains = {
        "WBR":        "Performance",
        "Meeting":    "Decision",
        "Pipeline":   "Commercial",
        "Initiative": "Strategic",
    }
    cols = st.columns(4)
    for i, (tool, domain) in enumerate(domains.items()):
        with cols[i]:
            is_present = tool in tool_outputs
            color = "#2d6a4f" if is_present else "#888888"
            bg = "#d8f3dc" if is_present else "#f8f8f8"
            border = "#2d6a4f" if is_present else "#dddddd"
            icon = "🟢" if is_present else "⚪"
            status = "Present" if is_present else "Not provided"
            st.markdown(
                f"""<div style='text-align:center; padding:12px;
                    border:1px solid {border}; border-radius:6px; background:{bg}'>
                    <div style='font-size:20px'>{icon}</div>
                    <div style='font-weight:600; color:{color}; font-size:13px'>{domain}</div>
                    <div style='font-size:11px; color:#888'>{tool}</div>
                    <div style='font-size:11px; color:{color}'>{status}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    missing = [t for t in domains if t not in tool_outputs]
    if missing:
        missing_domains = [domains[t] for t in missing]
        st.caption(
            f"⚠ {', '.join(missing_domains)} signal(s) not provided. "
            f"Convergence analysis reflects available domains only."
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

def render_attention_findings(attention_findings: list):
    """
    Cards are created from deterministic data.
    Claude-generated text fills synthesis and required_action.
    If empty, section notes no convergent themes — not a blank page.
    """
    if not attention_findings:
        st.info(
            "No convergent themes detected above threshold in the provided signals. "
            "All findings have time pressure and appear in Decision Cannot Be Postponed."
        )
        return

    for finding in attention_findings:
        with st.container():
            st.markdown(
                f"<h4 style='margin-bottom:4px'>▸ {finding['theme_label']}</h4>",
                unsafe_allow_html=True,
            )
            render_badges(finding.get("badge_sources", []))
            st.markdown("")

            synthesis = finding.get("synthesis", "")
            if synthesis:
                st.markdown(escape_dollars(synthesis))
            else:
                st.caption("_Narrative generation failed — see contributing signals below._")
                for s in finding.get("signals", [])[:3]:
                    st.caption(f"· {s['text'][:120]}")

            required_action = finding.get("required_action", "")
            if required_action:
                st.markdown(f"**Required action:** {escape_dollars(required_action)}")

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

            synthesis = finding.get("synthesis", "")
            if synthesis:
                st.markdown(escape_dollars(synthesis))
            else:
                st.caption("_Narrative generation failed — see contributing signals below._")
                for s in finding.get("signals", [])[:3]:
                    st.caption(f"· {s['text'][:120]}")

            col1, col2 = st.columns(2)
            with col1:
                decision = finding.get("decision_required", "")
                if decision:
                    st.markdown(f"**Decision required:** {escape_dollars(decision)}")
            with col2:
                deadline = finding.get("deadline_reference", "")
                if deadline:
                    st.markdown(f"**Deadline:** {escape_dollars(deadline)}")

            consequence = finding.get("consequence_of_deferral", "")
            if consequence:
                st.markdown(
                    f"<div style='background:#fef2f2; padding:10px; "
                    f"border-left:3px solid #b91c1c; border-radius:4px; "
                    f"font-size:13px; color:#7f1d1d; margin-top:8px'>"
                    f"⚠ {escape_dollars(consequence)}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")


# ── What the Signals Suggest ──────────────────────────────────────────────────

CONFIDENCE_COLORS = {
    "High":   ("#1b4332", "#d8f3dc"),
    "Medium": ("#5c2d0e", "#fde8d0"),
    "Low":    ("#5c1e1e", "#fde8d0"),
}

def render_signal_observation(signal_observation: dict):
    if not signal_observation:
        st.info("Structural observation unavailable — insufficient convergent signal.")
        return

    # Confidence indicator
    level = signal_observation.get("confidence_level", "")
    reason = signal_observation.get("confidence_reason", "")
    if level:
        fg, bg = CONFIDENCE_COLORS.get(level, ("#333", "#eee"))
        st.markdown(
            f"<div style='margin-bottom:12px'>"
            f"<span style='background:{bg}; color:{fg}; padding:3px 10px; "
            f"border-radius:12px; font-size:11px; font-weight:600'>"
            f"Observation Confidence: {level}</span>"
            f"<span style='font-size:11px; color:#666; margin-left:8px'>{reason}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Three-part hypothesis
    st.markdown(
        "<div style='background:#fafafa; border:1px solid #e5e7eb; "
        "border-radius:8px; padding:20px; margin-top:4px'>",
        unsafe_allow_html=True,
    )

    observed = signal_observation.get("observed_pattern", "")
    belief = signal_observation.get("likely_implicit_belief", "")
    alternative = signal_observation.get("alternative_explanation", "")

    if observed:
        st.markdown("**Observed Pattern**")
        st.markdown(escape_dollars(observed))
        st.markdown("")

    if belief:
        st.markdown("**Likely Implicit Belief**")
        st.markdown(
            f"<div style='color:#374151; font-style:italic'>"
            f"{escape_dollars(belief)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    if alternative:
        st.markdown("**Alternative Explanation**")
        st.markdown(
            f"<div style='background:#eff6ff; padding:12px; border-radius:6px; "
            f"border-left:3px solid #3b82f6; font-size:13px'>"
            f"{escape_dollars(alternative)}</div>",
            unsafe_allow_html=True,
        )

    if not any([observed, belief, alternative]):
        st.caption("_Observation generation failed — insufficient signal for structural hypothesis._")

    st.markdown("</div>", unsafe_allow_html=True)


# ── Watch Items ───────────────────────────────────────────────────────────────

def render_watch_items(watch_items: list, has_capped_findings: bool = False):
    if not watch_items:
        return

    label = f"Watch Items — {len(watch_items)} pattern(s)"
    with st.expander(label):
        if has_capped_findings:
            st.info(
                "Some findings above the convergence threshold were moved here to keep the "
                "primary output focused. If the top findings don't reflect your primary concern, "
                "review the scores below — a high-scoring item here may be more relevant for your situation."
            )
        else:
            st.caption(
                "These themes have signal but do not yet meet the convergence threshold "
                "(score ≥ 6, distinct tools ≥ 2). Scores shown for reference."
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
    """
    Main entry point. All sections render from deterministic data.
    Claude text fills cards. Fallback renders if Claude failed.
    """

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
    st.subheader("What the Signals Suggest")
    render_signal_observation(reasoning_output.get("signal_observation"))
    st.markdown("")

    # Watch Items
    watch = findings.get("watch", [])
    if watch:
        # has_capped_findings is True when Watch contains items that scored above
        # threshold but were deprioritized by the output cap
        all_scores = findings.get("all_scores", {})
        capped = any(
            info["score"] >= 6 and info["distinct_tool_count"] >= 2
            for item in watch
            for theme, info in [(item["theme"], all_scores.get(item["theme"], {}))]
            if info
        )
        render_watch_items(watch, has_capped_findings=capped)
