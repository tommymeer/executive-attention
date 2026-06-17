"""
claude_reasoning.py
Executive Attention Synthesizer — Claude Reasoning Layer

Architecture:
  - Attention + decision bundle calls run concurrently (ThreadPoolExecutor)
  - Observation call runs after, sequentially (needs full convergence picture)
  - All calls return plain JSON — no tool use
  - Deterministic layer owns structure; Claude owns language
  - Fallback text if any call fails — cards always render

Observation confidence is computed deterministically.
Claude writes the reason. Claude does not decide the level.
"""

import os
import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
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
            "Convergence detected across 2 organizational domains. "
            "Additional signal inputs may sharpen or revise this observation."
        )
    else:
        level = "Low"
        reason = (
            "Observation generated from a single organizational domain. "
            "Cross-domain corroboration is absent — treat as directional only."
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
- Be concise. Synthesis: 2-3 sentences. Required action: 1 sentence.

{company_framing}
{stage_framing}
{optional_section}"""


# ── Per-bundle prompts ────────────────────────────────────────────────────────

def build_attention_prompt(bundle: str) -> str:
    return f"""Write the narrative for this Requires Attention Now finding.

{bundle}

Return JSON only. No preamble, no explanation, no markdown fences.
{{
  "synthesis": "2-3 sentences max. The cross-domain pattern, what it implies, what is at stake.",
  "required_action": "1 sentence. Specific action required. Not monitor. A decision or intervention."
}}"""


def build_decision_prompt(bundle: str) -> str:
    return f"""Write the narrative for this Decision Cannot Be Postponed finding.

{bundle}

Return JSON only. No preamble, no explanation, no markdown fences.
{{
  "synthesis": "2-3 sentences max. The convergence and time constraint. What is converging and when it becomes irreversible.",
  "decision_required": "The specific decision that must be made. Not a monitoring task.",
  "deadline_reference": "The named date or window from the signals. Verbatim where possible.",
  "consequence_of_deferral": "1 sentence. What changes and cannot be recovered if deferred."
}}"""


def build_observation_prompt(top_themes: list, confidence_level: str,
                              confidence_reason: str) -> str:
    bundle_text = "\n\n".join(
        item.get("bundle", "") for item in top_themes
    )
    return f"""Produce the structural observation for What the Signals Suggest.

This is not a summary. Identify what the cross-domain convergence most strongly implies,
what alternative explanation could account for the same signals, and what remains
unresolvable without additional data.

Observation confidence (computed deterministically): {confidence_level}
Reason: {confidence_reason}

Signal bundles:
{bundle_text}

Return JSON only. No preamble, no explanation, no markdown fences.
{{
  "primary_hypothesis": "The explanation most supported by cross-domain convergence. Strictly tied to the highest-scoring signals. No narrative — just what the data most strongly implies. May include compound causality if convergence indicates multiple linked drivers. Do not force single-cause explanations.",
  "competing_hypothesis": "A plausible alternative explanation for the same signals. Must explain the same convergent pattern differently, not introduce new data.",
  "unresolved_ambiguity": "What cannot be determined from the signals available. Name specifically what data or signal would change the interpretation — and which hypothesis it would support. If no such data exists, explicitly state that the ambiguity is structural (not data-limited)."
}}"""


# ── Claude call with fallback ─────────────────────────────────────────────────

def call_claude_json(client, system_prompt: str, user_prompt: str,
                     max_tokens: int = 800) -> dict | None:
    """Single Claude call expecting JSON. Returns parsed dict or None on failure."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
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
    tools = item["score_info"]["distinct_tools"]
    return {
        "synthesis": (
            f"Convergent signals across {', '.join(tools)} point to "
            f"{item['theme_label']}. Contributing signals: {signal_text}"
        ),
        "required_action": (
            f"Review {item['theme_label']} signals and determine required intervention."
        ),
    }


def decision_fallback(item: dict) -> dict:
    signals = item.get("signals", [])
    signal_text = " · ".join(s["text"][:80] for s in signals[:3])
    time_ref = item.get("time_reference", "near term")
    return {
        "synthesis": (
            f"Convergent signals across {item['score_info']['distinct_tool_count']} "
            f"domains point to {item['theme_label']} with time pressure: {time_ref}. "
            f"Signals: {signal_text}"
        ),
        "decision_required": f"Make an explicit decision on {item['theme_label']} before {time_ref}.",
        "deadline_reference": time_ref,
        "consequence_of_deferral": (
            f"Continued deferral on {item['theme_label']} compounds risk as the deadline approaches."
        ),
    }


def observation_fallback(top_themes: list, confidence_level: str,
                          confidence_reason: str) -> dict:
    themes = ", ".join(item["theme_label"] for item in top_themes)
    tools = set()
    for item in top_themes:
        tools.update(item["score_info"].get("distinct_tools", []))
    return {
        "primary_hypothesis": (
            f"Convergent signals across {themes} and {', '.join(sorted(tools))} "
            f"point to a shared underlying constraint. The cross-domain pattern "
            f"suggests these are not independent issues."
        ),
        "competing_hypothesis": (
            "The same signals could reflect independent execution failures across "
            "domains rather than a single root cause — coincident pressure rather "
            "than structural convergence."
        ),
        "unresolved_ambiguity": (
            "Insufficient signal to distinguish root-cause convergence from "
            "correlated-but-independent failures. Additional data from missing "
            "organizational domains would clarify which hypothesis holds."
        ),
    }


# ── Concurrent bundle processor ───────────────────────────────────────────────

def process_bundle(args: tuple) -> tuple:
    """
    Worker function for ThreadPoolExecutor.
    Returns (index, finding_type, result_dict).
    """
    idx, finding_type, item, system_prompt, client = args
    bundle = item.get("bundle", "")

    if finding_type == "attention":
        result = call_claude_json(client, system_prompt,
                                  build_attention_prompt(bundle), max_tokens=600)
        if not result:
            result = attention_fallback(item)
        return (idx, "attention", item, result)

    elif finding_type == "decision":
        result = call_claude_json(client, system_prompt,
                                  build_decision_prompt(bundle), max_tokens=600)
        if not result:
            result = decision_fallback(item)
        return (idx, "decision", item, result)


# ── Master reasoning runner ───────────────────────────────────────────────────

def run_reasoning(findings: dict, business_context: dict) -> dict:
    """
    Concurrent Claude calls for all bundle findings.
    Sequential observation call after.

    Pass 1 (concurrent): all attention + decision bundles run in parallel.
    Pass 2 (sequential): structural observation, forced after pass 1 completes.

    Fallback text renders if any call fails.
    Cards always exist. Claude only fills language.
    """
    client = get_client()
    system_prompt = build_system_prompt(business_context)

    attention_items = findings.get("requires_attention", [])
    decision_items = findings.get("cannot_postpone", [])

    # Build work queue — (index, type, item, system_prompt, client)
    work = []
    for i, item in enumerate(attention_items):
        work.append((i, "attention", item, system_prompt, client))
    for i, item in enumerate(decision_items):
        work.append((i, "decision", item, system_prompt, client))

    # ── Pass 1: Concurrent bundle calls ──────────────────────────────────────
    attention_results = [None] * len(attention_items)
    decision_results = [None] * len(decision_items)

    max_workers = min(len(work), 6)  # cap at 6 concurrent calls

    if work:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_bundle, w): w for w in work}
            for future in as_completed(futures):
                try:
                    idx, finding_type, item, result = future.result()
                    if finding_type == "attention":
                        attention_results[idx] = (item, result)
                    elif finding_type == "decision":
                        decision_results[idx] = (item, result)
                except Exception:
                    pass  # fallback text will render for failed items

    # Build attention findings list
    attention_findings = []
    for i, item in enumerate(attention_items):
        pair = attention_results[i]
        if pair:
            original_item, result = pair
        else:
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

    # Build decision findings list
    decision_findings = []
    for i, item in enumerate(decision_items):
        pair = decision_results[i]
        if pair:
            original_item, result = pair
        else:
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

    # ── Pass 2: Observation (sequential, after pass 1 completes) ─────────────
    top_themes = findings.get("top_for_observation", [])
    confidence_level, confidence_reason = compute_observation_confidence(top_themes)

    obs_result = call_claude_json(
        client, system_prompt,
        build_observation_prompt(top_themes, confidence_level, confidence_reason),
        max_tokens=800,
    )
    if not obs_result:
        obs_result = observation_fallback(top_themes, confidence_level, confidence_reason)

    signal_observation = {
        "primary_hypothesis": obs_result.get("primary_hypothesis", ""),
        "competing_hypothesis": obs_result.get("competing_hypothesis", ""),
        "unresolved_ambiguity": obs_result.get("unresolved_ambiguity", ""),
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
    }

    return {
        "attention_findings": attention_findings,
        "decision_findings": decision_findings,
        "signal_observation": signal_observation,
    }
