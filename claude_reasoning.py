"""
claude_reasoning.py
Executive Attention Synthesizer — Claude Reasoning Layer

Architecture:
  - One Claude call per bundle (attention + decision findings)
  - One Claude call for structural observation (JSON, no tool use)
  - Deterministic layer owns structure; Claude owns language
  - Fallback text if any call fails — cards always render

Observation confidence is computed deterministically and passed to Claude.
Claude writes the reason. Claude does not decide the level.
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


# ── Observation confidence (deterministic) ────────────────────────────────────

def compute_observation_confidence(top_themes: list) -> tuple:
    """
    Computes confidence level for the structural observation.
    Based on distinct tool count across top convergent themes.
    Returns (level, reason) — Claude receives both and writes the display reason.
    """
    if not top_themes:
        return "Low", "No convergent themes available for structural observation."

    max_tools = max(
        item["score_info"]["distinct_tool_count"]
        for item in top_themes
    )
    total_signals = sum(
        item["score_info"]["signal_count"]
        for item in top_themes
    )
    theme_count = len(top_themes)

    if max_tools >= 3:
        level = "High"
        reason = (
            f"{theme_count} convergent theme(s) with signal from "
            f"{max_tools} distinct organizational domains."
        )
    elif max_tools == 2:
        level = "Medium"
        reason = (
            f"Convergence detected across 2 organizational domains. "
            f"Additional signal inputs may sharpen or revise this observation."
        )
    else:
        level = "Low"
        reason = (
            f"Observation generated from a single organizational domain. "
            f"Cross-domain corroboration is absent — treat as directional only."
        )

    return level, reason


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
            "acquisition efficiency. Avoid enterprise procurement framing unless directly "
            "present in signals."
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
ADDITIONAL BUSINESS CONTEXT:
{optional_context}

Use this as an interpretive anchor where relevant. Do not fabricate signals from it.
"""

    return f"""You are writing narrative for the Executive Attention Synthesizer.

The structure of every finding has already been determined by a deterministic convergence engine.
Your only job is to write the language that explains what each convergence means.

WHAT YOU ARE NOT DOING:
- Do not decide what is important. That has already been decided.
- Do not invent signals not present in the bundle.
- Do not produce generic language ("leadership should monitor this").
- Do not summarize each tool separately — synthesize across them.

SPECIFICITY REQUIREMENTS:
- Name the specific theme and the specific signals supporting it.
- Every action or decision must be concrete — not "monitor" or "discuss."
- Quantify where signals provide numbers.
- Badge sources are already determined — do not reassign them.

{company_framing}
{stage_framing}
{optional_section}"""


# ── Per-bundle prompts ────────────────────────────────────────────────────────

def build_attention_prompt(bundle: str) -> str:
    return f"""Write the narrative for this Requires Attention Now finding.

{bundle}

Return JSON only. No preamble, no explanation, no markdown fences.
Exact format:
{{
  "synthesis": "2-3 sentences. Names the cross-domain pattern, what each signal shows, what they together imply.",
  "required_action": "1 sentence. Specific action required. Not monitor. A decision or intervention."
}}"""


def build_decision_prompt(bundle: str) -> str:
    return f"""Write the narrative for this Decision Cannot Be Postponed finding.

{bundle}

Return JSON only. No preamble, no explanation, no markdown fences.
Exact format:
{{
  "synthesis": "2-3 sentences. Names the convergence and time constraint. What is converging and when it becomes irreversible.",
  "decision_required": "The specific decision that must be made. Not a monitoring task.",
  "deadline_reference": "The named date or window from the signals. Verbatim where possible.",
  "consequence_of_deferral": "1 sentence. What changes and cannot be recovered if this is deferred."
}}"""


def build_observation_prompt(top_themes: list, confidence_level: str,
                              confidence_reason: str) -> str:
    bundle_text = "\n\n".join(
        item.get("bundle", "") for item in top_themes
    )
    return f"""Produce the structural observation for What the Signals Suggest.

This is not a summary of findings. Identify the tension between:
- What the organization appears to believe is true (based on where attention and resources are concentrated)
- What the convergent signals suggest is actually true

The observation confidence has been computed deterministically:
Confidence: {confidence_level}
Reason: {confidence_reason}

Signal bundles:
{bundle_text}

Return JSON only. No preamble, no explanation, no markdown fences.
Exact format:
{{
  "observed_pattern": "What the signals show is happening across organizational domains. Observable fact, not interpretation. Name specific domains.",
  "likely_implicit_belief": "What the organization appears to be assuming is true. Start with: Leadership appears to be operating as though...",
  "alternative_explanation": "A plausible reframe the data supports. Not a correction — a hypothesis. Start with: An alternative explanation is... or The data is also consistent with..."
}}"""


# ── Claude call with fallback ─────────────────────────────────────────────────

def call_claude_json(client, system_prompt: str, user_prompt: str,
                     max_tokens: int = 1000) -> dict | None:
    """
    Single Claude call expecting JSON response.
    Returns parsed dict or None on failure.
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown fences if present despite instructions
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return None


# ── Fallback text builders ────────────────────────────────────────────────────

def attention_fallback(item: dict) -> dict:
    signals = item.get("signals", [])
    signal_text = " · ".join(s["text"][:80] for s in signals[:3])
    return {
        "synthesis": (
            f"Multiple organizational domains are signaling a convergence on "
            f"{item['theme_label']}. Contributing signals: {signal_text}"
        ),
        "required_action": (
            f"Review the {item['theme_label']} signals across "
            f"{', '.join(item['score_info']['distinct_tools'])} and determine the required intervention."
        ),
    }


def decision_fallback(item: dict) -> dict:
    signals = item.get("signals", [])
    signal_text = " · ".join(s["text"][:80] for s in signals[:3])
    time_ref = item.get("time_reference", "near term")
    return {
        "synthesis": (
            f"Convergent signals across {len(item['score_info']['distinct_tools'])} "
            f"organizational domains point to {item['theme_label']} with time pressure: {time_ref}. "
            f"Contributing signals: {signal_text}"
        ),
        "decision_required": f"Make an explicit decision on {item['theme_label']} before {time_ref}.",
        "deadline_reference": time_ref,
        "consequence_of_deferral": (
            f"Continued deferral on {item['theme_label']} increases risk as the "
            f"{time_ref} constraint approaches."
        ),
    }


def observation_fallback(top_themes: list, confidence_level: str,
                          confidence_reason: str) -> dict:
    themes = ", ".join(item["theme_label"] for item in top_themes)
    tools = set()
    for item in top_themes:
        tools.update(item["score_info"].get("distinct_tools", []))
    return {
        "observed_pattern": (
            f"Convergent signals detected across {themes}. "
            f"Contributing domains: {', '.join(sorted(tools))}."
        ),
        "likely_implicit_belief": (
            "Leadership appears to be operating as though these organizational signals "
            "are independent. The convergence pattern suggests they share a common root."
        ),
        "alternative_explanation": (
            "The data is also consistent with a single underlying constraint "
            "manifesting across multiple organizational systems simultaneously."
        ),
    }


# ── Master reasoning runner ───────────────────────────────────────────────────

def run_reasoning(findings: dict, business_context: dict) -> dict:
    """
    Main entry point.

    For each attention bundle: one Claude call → synthesis + required_action
    For each decision bundle: one Claude call → synthesis + decision fields
    For observation: one Claude call → three-part hypothesis + confidence

    Fallback text renders if any call fails.
    Cards always exist. Claude only fills language.
    """
    client = get_client()
    system_prompt = build_system_prompt(business_context)

    # ── Attention findings — one call per bundle ──────────────────────────────
    attention_findings = []
    for item in findings.get("requires_attention", []):
        bundle = item.get("bundle", "")
        result = call_claude_json(
            client, system_prompt,
            build_attention_prompt(bundle),
            max_tokens=800,
        )
        if not result:
            result = attention_fallback(item)

        attention_findings.append({
            "theme": item["theme"],
            "theme_label": item["theme_label"],
            "synthesis": result.get("synthesis", ""),
            "required_action": result.get("required_action", ""),
            "badge_sources": sorted(set(
                s["source_tool"] for s in item.get("signals", [])
            )),
            "score": item["score"],
            "score_info": item["score_info"],
        })

    # ── Decision findings — one call per bundle ───────────────────────────────
    decision_findings = []
    for item in findings.get("cannot_postpone", []):
        bundle = item.get("bundle", "")
        result = call_claude_json(
            client, system_prompt,
            build_decision_prompt(bundle),
            max_tokens=800,
        )
        if not result:
            result = decision_fallback(item)

        decision_findings.append({
            "theme": item["theme"],
            "theme_label": item["theme_label"],
            "synthesis": result.get("synthesis", ""),
            "decision_required": result.get("decision_required", ""),
            "deadline_reference": result.get("deadline_reference", ""),
            "consequence_of_deferral": result.get("consequence_of_deferral", ""),
            "badge_sources": sorted(set(
                s["source_tool"] for s in item.get("signals", [])
            )),
            "score": item["score"],
            "score_info": item["score_info"],
        })

    # ── Structural observation — one call, confidence deterministic ───────────
    top_themes = findings.get("top_for_observation", [])
    confidence_level, confidence_reason = compute_observation_confidence(top_themes)

    obs_result = call_claude_json(
        client, system_prompt,
        build_observation_prompt(top_themes, confidence_level, confidence_reason),
        max_tokens=1000,
    )
    if not obs_result:
        obs_result = observation_fallback(top_themes, confidence_level, confidence_reason)

    signal_observation = {
        "observed_pattern": obs_result.get("observed_pattern", ""),
        "likely_implicit_belief": obs_result.get("likely_implicit_belief", ""),
        "alternative_explanation": obs_result.get("alternative_explanation", ""),
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
    }

    return {
        "attention_findings": attention_findings,
        "decision_findings": decision_findings,
        "signal_observation": signal_observation,
    }
