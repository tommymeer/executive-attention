"""
claude_reasoning.py
Executive Attention Synthesizer — Claude Reasoning Layer

Single-pass Claude API call over signal bundles.
Claude receives structured bundles — never raw tool output.
Three structured tools: attention finding, decision finding, signal observation.
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()


# ── Anthropic client ──────────────────────────────────────────────────────────

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set.")
    return anthropic.Anthropic(api_key=api_key)


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "write_attention_finding",
        "description": (
            "Write a Requires Attention Now finding. "
            "Names the specific convergence, what it implies, and what action it requires. "
            "Never generic. Always specific to the signals provided."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "Canonical theme name"},
                "theme_label": {"type": "string", "description": "Human-readable theme label"},
                "synthesis": {
                    "type": "string",
                    "description": (
                        "2-3 sentences. Names the specific cross-domain pattern. "
                        "What each contributing signal shows. What they together imply. "
                        "Calibrated to company type and stage."
                    )
                },
                "required_action": {
                    "type": "string",
                    "description": (
                        "1 sentence. The specific action this convergence requires. "
                        "Not 'monitor'. A decision or intervention."
                    )
                },
                "badge_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of source tool names that contributed signals."
                },
            },
            "required": ["theme", "theme_label", "synthesis", "required_action", "badge_sources"],
        },
    },
    {
        "name": "write_decision_finding",
        "description": (
            "Write a Decision Cannot Be Postponed finding. "
            "Same as attention finding, but with explicit deadline naming "
            "and consequence of deferral."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string"},
                "theme_label": {"type": "string"},
                "synthesis": {
                    "type": "string",
                    "description": (
                        "2-3 sentences. Names the convergence and time constraint. "
                        "What is converging and when it becomes irreversible."
                    )
                },
                "decision_required": {
                    "type": "string",
                    "description": "The specific decision that must be made. Not a monitoring task."
                },
                "deadline_reference": {
                    "type": "string",
                    "description": "The named date or window from the signals. Verbatim if possible."
                },
                "consequence_of_deferral": {
                    "type": "string",
                    "description": "1 sentence. What changes — and cannot be recovered — if this is deferred."
                },
                "badge_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "theme", "theme_label", "synthesis", "decision_required",
                "deadline_reference", "consequence_of_deferral", "badge_sources"
            ],
        },
    },
    {
        "name": "write_signal_observation",
        "description": (
            "Write the What the Signals Suggest structural hypothesis. "
            "Three named components: observed pattern, likely implicit belief, alternative explanation. "
            "Not a summary. Surfaces what the organization appears to believe vs. "
            "what the convergent signals suggest is actually true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "observed_pattern": {
                    "type": "string",
                    "description": (
                        "What the signals show is happening across organizational domains. "
                        "Stated as observable fact, not interpretation. "
                        "Name the specific domains and what each shows."
                    )
                },
                "likely_implicit_belief": {
                    "type": "string",
                    "description": (
                        "What the organization appears to be assuming is true, "
                        "based on where attention and resources are concentrated. "
                        "Framed as 'Leadership appears to be operating as though...'"
                    )
                },
                "alternative_explanation": {
                    "type": "string",
                    "description": (
                        "A plausible reframe the data supports. "
                        "Not a correction — a hypothesis. "
                        "Framed as 'An alternative explanation is...' or 'The data is also consistent with...'"
                    )
                },
            },
            "required": ["observed_pattern", "likely_implicit_belief", "alternative_explanation"],
        },
    },
]


# ── System prompt ─────────────────────────────────────────────────────────────

def build_system_prompt(business_context: dict) -> str:
    company_type = business_context.get("company_type", "")
    stage = business_context.get("stage", "")
    optional_context = business_context.get("optional_context", "")

    company_framing = ""
    if company_type == "Consumer":
        company_framing = (
            "This is a consumer business. Frame findings in language relevant to "
            "consumer metrics: activation, retention, cohort behavior, product engagement, "
            "acquisition efficiency. Avoid enterprise procurement framing unless directly present in signals."
        )
    elif company_type == "Enterprise / B2B":
        company_framing = (
            "This is an enterprise or B2B business. Frame findings in language relevant to "
            "enterprise motion: pipeline, procurement, compliance, expansion, account health, "
            "sales capacity. Quantify where signals provide numbers."
        )
    elif company_type == "Mixed":
        company_framing = (
            "This is a mixed business serving both enterprise and consumer segments. "
            "Frame findings to reflect the segment most implicated by each convergence."
        )

    stage_framing = ""
    if "Series B" in stage or "Series C" in stage or "Scaling" in stage:
        stage_framing = (
            "This company is scaling. Findings should reflect the execution and alignment "
            "challenges of a company growing through complexity — not survival-mode framing."
        )
    elif "Series A" in stage or "Early" in stage:
        stage_framing = (
            "This is an early-stage company. Findings should reflect the focus and "
            "prioritization challenges of a company still establishing product-market fit "
            "and initial go-to-market motion."
        )
    elif "Pre-revenue" in stage:
        stage_framing = (
            "This is a pre-revenue company. Findings should reflect the resource constraints "
            "and strategic alignment challenges of a company still validating its direction."
        )
    elif "Growth" in stage or "Late" in stage:
        stage_framing = (
            "This is a growth-stage company. Findings should reflect the operational "
            "complexity and organizational alignment challenges of a scaled organization."
        )

    optional_section = ""
    if optional_context:
        optional_section = f"""
ADDITIONAL BUSINESS CONTEXT PROVIDED BY USER:
{optional_context}

Use this as an interpretive anchor where relevant. If convergent signals connect to 
this context, make that connection explicit. Do not fabricate signals from this context.
"""

    return f"""You are analyzing convergent organizational signals for the Executive Attention Synthesizer.

You receive structured signal bundles — preprocessed, scored, and classified by a deterministic convergence engine. 
Your job is translation and structural observation, not classification or scoring.

WHAT YOU ARE NOT DOING:
- Do not re-classify findings. Classification has already been done deterministically.
- Do not invent signals not present in the bundles.
- Do not produce generic risk language ("leadership should monitor this area").
- Do not summarize what each tool found separately — synthesize across them.

WHAT YOU ARE DOING:
- For Requires Attention Now findings: name the specific cross-domain pattern, what it implies, and what action it requires.
- For Decision Cannot Be Postponed findings: name the convergence, the specific decision, the deadline, and what deferral costs.
- For What the Signals Suggest: produce the three-part structural hypothesis. Surface the tension between what the organization appears to believe and what the signals suggest is true.

SPECIFICITY REQUIREMENTS:
- Every finding must name the specific theme and the specific signals supporting it.
- Every action or decision must be specific — not "monitor" or "discuss."
- Quantify where the signals provide numbers. "Enterprise win rate down 18%" is better than "enterprise win rate declining."
- Attribution is deterministic — badge sources come from the bundle, not from your judgment.

ABSENCE AS EVIDENCE:
- If a theme scores high but a key organizational domain is absent from contributing signals, note the gap.
- "Enterprise readiness is flagged in performance, pipeline, and execution — but no decision signal is present, 
  suggesting this pattern has not yet surfaced in leadership conversation" is valuable.

HYPOTHESIS FRAMING:
- What the Signals Suggest is not a summary. It is a structural observation.
- The alternative explanation is a plausible reframe, not a correction. Frame as hypothesis.
- If no genuine tension is visible in the bundles, say so rather than manufacturing one.

{company_framing}

{stage_framing}

{optional_section}

Use the provided tools to structure your output. Use write_attention_finding for each Requires Attention Now finding,
write_decision_finding for each Decision Cannot Be Postponed finding, and write_signal_observation once for 
What the Signals Suggest (based on the top convergent themes provided)."""


# ── User prompt builder ───────────────────────────────────────────────────────

def build_user_prompt(findings: dict) -> str:
    sections = []

    if findings.get("requires_attention"):
        sections.append("=== REQUIRES ATTENTION NOW — Signal Bundles ===\n")
        for item in findings["requires_attention"]:
            sections.append(item.get("bundle", ""))
            sections.append("")

    if findings.get("cannot_postpone"):
        sections.append("=== DECISION CANNOT BE POSTPONED — Signal Bundles ===\n")
        for item in findings["cannot_postpone"]:
            sections.append(item.get("bundle", ""))
            sections.append("")

    if findings.get("top_for_observation"):
        sections.append("=== WHAT THE SIGNALS SUGGEST — Top Convergent Bundles ===\n")
        sections.append(
            "Use these bundles to produce the three-part structural hypothesis. "
            "Do not summarize — identify the tension between implicit belief and signal reality.\n"
        )
        for item in findings["top_for_observation"]:
            sections.append(item.get("bundle", ""))
            sections.append("")

    if not sections:
        return (
            "No convergent themes were detected above the threshold in the provided signals. "
            "Please call write_signal_observation with an observed_pattern noting the absence of "
            "convergent findings, and suggest what additional signal inputs might surface patterns."
        )

    return "\n".join(sections)


# ── Response parser ───────────────────────────────────────────────────────────

def parse_tool_calls(response) -> dict:
    """Extract structured outputs from Claude's tool use response."""
    attention_findings = []
    decision_findings = []
    signal_observation = None

    for block in response.content:
        if block.type != "tool_use":
            continue

        name = block.name
        inp = block.input

        if name == "write_attention_finding":
            attention_findings.append({
                "theme": inp.get("theme", ""),
                "theme_label": inp.get("theme_label", ""),
                "synthesis": inp.get("synthesis", ""),
                "required_action": inp.get("required_action", ""),
                "badge_sources": inp.get("badge_sources", []),
            })

        elif name == "write_decision_finding":
            decision_findings.append({
                "theme": inp.get("theme", ""),
                "theme_label": inp.get("theme_label", ""),
                "synthesis": inp.get("synthesis", ""),
                "decision_required": inp.get("decision_required", ""),
                "deadline_reference": inp.get("deadline_reference", ""),
                "consequence_of_deferral": inp.get("consequence_of_deferral", ""),
                "badge_sources": inp.get("badge_sources", []),
            })

        elif name == "write_signal_observation":
            signal_observation = {
                "observed_pattern": inp.get("observed_pattern", ""),
                "likely_implicit_belief": inp.get("likely_implicit_belief", ""),
                "alternative_explanation": inp.get("alternative_explanation", ""),
            }

    return {
        "attention_findings": attention_findings,
        "decision_findings": decision_findings,
        "signal_observation": signal_observation,
    }


# ── Master reasoning runner ───────────────────────────────────────────────────

def run_reasoning(findings: dict, business_context: dict) -> dict:
    """
    Main entry point for the Claude reasoning layer.
    Takes classified and bundled findings + business context.
    Returns parsed structured output.
    """
    client = get_client()

    system_prompt = build_system_prompt(business_context)
    user_prompt = build_user_prompt(findings)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,
        tools=TOOLS,
        tool_choice={"type": "any"},
        messages=[
            {"role": "user", "content": user_prompt}
        ],
    )

    return parse_tool_calls(response)
