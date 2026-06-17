"""
app.py
Executive Attention Synthesizer — Cross-Signal Convergence Detection
thomasmeerschwam.com

Identifies where multiple organizational realities are pointing at the same underlying problem.
"""

import streamlit as st
import os
from dotenv import load_dotenv

from signal_extraction import extract_signals, summarize_extraction
from convergence import run_convergence
from claude_reasoning import run_reasoning
from export import build_export
from components.output_display import render_full_output

load_dotenv()

st.set_page_config(
    page_title="Executive Attention Synthesizer",
    page_icon="◎",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("◎ Executive Attention Synthesizer")
st.markdown(
    "**Cross-Signal Convergence Detection** — identifies where multiple organizational "
    "realities are pointing at the same underlying problem."
)
st.markdown(
    "_Every system tells a different story. "
    "The job isn't collecting more stories. It's finding the one they're all trying to tell._"
)
st.markdown("---")

# ── Session state ─────────────────────────────────────────────────────────────

for key in ["tool_outputs", "business_context", "signals", "extraction_summary",
            "findings", "reasoning_output"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Step 1: Business context ──────────────────────────────────────────────────

st.header("1 · Business Context")
st.caption("Takes 60 seconds. Calibrates output language and finding order to your business.")

col1, col2 = st.columns(2)

with col1:
    company_type = st.selectbox(
        "Company Type",
        options=["", "Enterprise / B2B", "Consumer", "Mixed", "Other"],
        index=0,
        help="Used to calibrate output language and finding order. Does not affect convergence scores.",
    )

with col2:
    stage = st.selectbox(
        "Stage",
        options=[
            "",
            "Pre-revenue / Pre-product-market fit",
            "Early revenue (Seed / Series A)",
            "Scaling (Series B / Series C)",
            "Growth / Late stage",
        ],
        index=0,
        help="Used to calibrate interpretive framing. Does not affect convergence scores.",
    )

optional_context = st.text_area(
    "Anything else we should know? (Optional)",
    placeholder=(
        "E.g. we're mid-way through a pricing transition, "
        "we recently reorganized GTM, "
        "retention is our primary focus this quarter."
    ),
    height=80,
    help="Passes to Claude as interpretive context. Does not affect convergence scores.",
)

context_complete = bool(company_type and stage)

if company_type and stage:
    st.session_state.business_context = {
        "company_type": company_type,
        "stage": stage,
        "optional_context": optional_context.strip(),
    }

# ── Step 2: Upload tool outputs ───────────────────────────────────────────────

if context_complete:
    st.markdown("---")
    st.header("2 · Upload Signal Inputs")
    st.caption(
        "Upload exported .txt outputs from any of the four Ground Truth tools. "
        "One input minimum — the tool finds convergence across whatever signals are available."
    )

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        wbr_file = st.file_uploader(
            "WBR Generator output",
            type=["txt"],
            help="Performance signal — what happened?",
            key="wbr_upload",
        )

    with col2:
        meeting_file = st.file_uploader(
            "Meeting Intelligence output",
            type=["txt"],
            help="Decision signal — what was decided?",
            key="meeting_upload",
        )

    with col3:
        pipeline_file = st.file_uploader(
            "Pipeline Synthesizer output",
            type=["txt"],
            help="Commercial signal — what will happen?",
            key="pipeline_upload",
        )

    with col4:
        initiative_file = st.file_uploader(
            "Initiative Intelligence output",
            type=["txt"],
            help="Strategic signal — are we executing?",
            key="initiative_upload",
        )

    # Read uploaded files
    tool_outputs = {}
    if wbr_file:
        tool_outputs["WBR"] = wbr_file.read().decode("utf-8", errors="ignore")
    if meeting_file:
        tool_outputs["Meeting"] = meeting_file.read().decode("utf-8", errors="ignore")
    if pipeline_file:
        tool_outputs["Pipeline"] = pipeline_file.read().decode("utf-8", errors="ignore")
    if initiative_file:
        tool_outputs["Initiative"] = initiative_file.read().decode("utf-8", errors="ignore")

    if tool_outputs:
        st.session_state.tool_outputs = tool_outputs

        # Coverage note for partial input
        missing = [t for t in ["WBR", "Meeting", "Pipeline", "Initiative"]
                   if t not in tool_outputs]
        domain_map = {
            "WBR": "Performance", "Meeting": "Decision",
            "Pipeline": "Commercial", "Initiative": "Strategic"
        }
        if missing:
            missing_domains = [domain_map[t] for t in missing]
            st.info(
                f"**{', '.join(missing_domains)} signal(s) not provided.** "
                f"Convergence analysis will reflect the {len(tool_outputs)} available "
                f"domain(s). Cross-domain findings may be understated. "
                f"You can still run — the tool works with partial signal."
            )
        else:
            st.success("All four organizational domains present. Full convergence analysis available.")

# ── Step 3: Run ───────────────────────────────────────────────────────────────

inputs_ready = bool(
    st.session_state.tool_outputs and
    context_complete
)

if inputs_ready:
    st.markdown("---")
    st.header("3 · Run Analysis")

    if st.button("◎ Run Convergence Analysis", type="primary", use_container_width=True):

        with st.spinner("Extracting signals from tool outputs..."):
            signals = extract_signals(st.session_state.tool_outputs)
            extraction_summary = summarize_extraction(signals, st.session_state.tool_outputs)
            st.session_state.signals = signals
            st.session_state.extraction_summary = extraction_summary

        with st.spinner("Computing theme convergence..."):
            findings = run_convergence(signals, st.session_state.business_context)
            st.session_state.findings = findings

        with st.spinner("Synthesizing findings..."):
            reasoning_output = run_reasoning(findings, st.session_state.business_context)
            st.session_state.reasoning_output = reasoning_output

        st.success("Analysis complete.")

# ── Step 4: Output ────────────────────────────────────────────────────────────

if st.session_state.reasoning_output and st.session_state.findings:
    st.markdown("---")
    st.header("4 · Executive Attention Report")

    render_full_output(
        st.session_state.reasoning_output,
        st.session_state.findings,
        st.session_state.tool_outputs,
    )

    # Export
    st.markdown("---")
    export_text = build_export(
        st.session_state.business_context,
        st.session_state.tool_outputs,
        st.session_state.findings,
        st.session_state.reasoning_output,
    )
    st.download_button(
        label="Download Report (.txt)",
        data=export_text,
        file_name="executive_attention_report.txt",
        mime="text/plain",
        use_container_width=True,
    )

    # Debug expander (remove before ship)
    with st.expander("Debug — Signal Extraction Summary", expanded=False):
        summary = st.session_state.extraction_summary
        if summary:
            st.json(summary)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    "Executive Attention Synthesizer · [thomasmeerschwam.com](https://thomasmeerschwam.com) · "
    "Part of the Ground Truth Decisioning System"
)
