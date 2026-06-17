"""
theme_config.py
Executive Attention Synthesizer — Theme Configuration

All theme keyword maps, synonym maps, and company-type ranking tables live here.
Extend this file to add coverage without touching core architecture.
"""

# ── Canonical theme taxonomy ──────────────────────────────────────────────────

CANONICAL_THEMES = [
    "enterprise_readiness",
    "go_to_market",
    "customer_retention",
    "product_reliability",
    "capacity_constraints",
    "pricing_strategy",
    "strategic_drift",
    "organizational_alignment",
    "execution_risk",
    "hiring_talent",
]

THEME_LABELS = {
    "enterprise_readiness":    "Enterprise Readiness",
    "go_to_market":            "Go-to-Market",
    "customer_retention":      "Customer Retention",
    "product_reliability":     "Product Reliability",
    "capacity_constraints":    "Capacity Constraints",
    "pricing_strategy":        "Pricing Strategy",
    "strategic_drift":         "Strategic Drift",
    "organizational_alignment":"Organizational Alignment",
    "execution_risk":          "Execution Risk",
    "hiring_talent":           "Hiring & Talent",
}

# ── Keyword maps ──────────────────────────────────────────────────────────────
# Each theme maps to a list of keywords/phrases.
# Signal text is lowercased before matching.

THEME_KEYWORDS = {
    "enterprise_readiness": [
        "enterprise", "compliance", "security", "procurement", "audit",
        "soc2", "soc 2", "hipaa", "gdpr", "iso", "certification",
        "enterprise readiness", "enterprise customer", "enterprise deal",
        "enterprise account", "enterprise sales", "upmarket", "up-market",
        "win rate", "win rates", "security review", "vendor review",
        "contract review", "legal review", "infosec", "penetration test",
        "pen test", "access control", "role-based", "rbac", "sso",
        "single sign-on", "saml", "stalled in procurement", "procurement friction",
        "procurement delay", "procurement stall", "enterprise segment",
        "enterprise motion", "land and expand", "expand motion",
    ],
    "go_to_market": [
        "gtm", "go-to-market", "go to market", "launch", "market coverage",
        "pipeline", "sales capacity", "sales motion", "demand generation",
        "demand gen", "top of funnel", "tofu", "outbound", "inbound",
        "lead generation", "lead gen", "pipeline generation", "pipeline coverage",
        "channel", "partner", "partnership", "distribution", "marketing",
        "campaign", "conversion", "funnel", "acquisition", "new logo",
        "new business", "net new", "bookings", "arr growth", "revenue growth",
        "quota", "territory", "segment", "market segment", "market expansion",
        "product launch", "go-live", "release", "rollout",
    ],
    "customer_retention": [
        "retention", "churn", "nrr", "net revenue retention", "gross retention",
        "grr", "expansion", "upsell", "cross-sell", "renewal", "renewals",
        "customer success", "cs", "onboarding", "activation", "engagement",
        "dau", "mau", "daily active", "monthly active", "stickiness",
        "cohort", "ltv", "lifetime value", "support volume", "support load",
        "escalation", "at-risk account", "at risk", "health score",
        "customer health", "qbr", "business review", "satisfaction", "nps",
        "csat", "churn rate", "logo churn", "revenue churn", "cancel",
        "cancellation", "lapse", "lapsed", "win-back", "reactivation",
    ],
    "product_reliability": [
        "incident", "p1", "p0", "outage", "downtime", "reliability",
        "uptime", "sla", "slo", "error rate", "latency", "performance",
        "bug", "defect", "regression", "crash", "failure", "degradation",
        "service degradation", "production issue", "production bug",
        "hotfix", "rollback", "incident response", "post-mortem", "postmortem",
        "on-call", "alert", "pager", "monitoring", "observability",
        "stability", "quality", "technical debt", "tech debt",
    ],
    "capacity_constraints": [
        "capacity", "bandwidth", "resourcing", "resource", "headcount",
        "availability", "overloaded", "stretched", "understaffed", "backlog",
        "bottleneck", "constraint", "blocked by capacity", "no capacity",
        "limited capacity", "resource constraint", "team capacity",
        "engineering capacity", "eng capacity", "design capacity",
        "sprint capacity", "velocity", "throughput", "cycle time",
        "lead time", "workload", "utilization",
    ],
    "pricing_strategy": [
        "pricing", "price", "packaging", "monetization", "discount",
        "discounting", "deal economics", "margin", "gross margin",
        "unit economics", "cac", "arpu", "arppu", "arpa", "acv",
        "average contract value", "deal size", "price increase",
        "price change", "repricing", "price sensitivity", "willingness to pay",
        "wtp", "tiering", "tier", "freemium", "free tier", "plan",
        "subscription", "pricing model", "revenue model", "billing",
        "payment", "contract structure",
    ],
    "strategic_drift": [
        "drift", "misalignment", "misaligned", "off-strategy", "off strategy",
        "strategic drift", "execution gap", "strategy gap", "priority shift",
        "priority change", "reprioritize", "deprioritize", "scope creep",
        "distraction", "not aligned", "no longer aligned", "diverged",
        "divergence", "lost focus", "focus", "strategic bet", "bet",
        "strategic priority", "original plan", "stated strategy",
        "stated priority", "planned vs actual", "plan vs actual",
    ],
    "organizational_alignment": [
        "ownership", "owner", "unowned", "no owner", "unclear ownership",
        "ownership gap", "role ambiguity", "ambiguity", "decision authority",
        "decision rights", "accountability", "responsible", "raci",
        "alignment", "misaligned teams", "cross-functional", "handoff",
        "coordination", "collaboration", "silos", "silo", "fragmented",
        "deferred", "deferral", "unresolved", "open question", "tbd",
        "to be decided", "pending decision", "no decision", "stuck",
        "organizational", "org design", "reporting structure",
    ],
    "execution_risk": [
        "delayed", "delay", "behind schedule", "behind plan", "slipping",
        "slip", "milestone", "missed milestone", "at risk", "execution risk",
        "delivery risk", "launch risk", "timeline", "deadline", "due date",
        "overdue", "late", "blocked", "blocker", "dependency", "blockers",
        "impediment", "risk", "initiative risk", "project risk",
        "program risk", "rollout risk", "not on track", "off track",
        "red", "amber", "yellow", "status red", "status yellow",
    ],
    "hiring_talent": [
        "hiring", "hire", "headcount", "hc", "recruiter", "recruiting",
        "recruitment", "open role", "open position", "unfilled", "vacancy",
        "backfill", "attrition", "turnover", "retention", "key person",
        "key hire", "critical hire", "talent", "talent gap", "skills gap",
        "onboarding", "ramp", "new hire", "offer", "offer accepted",
        "declined offer", "pipeline", "candidate", "interview",
    ],
}

# ── Severity language markers ─────────────────────────────────────────────────

SEVERITY_3_MARKERS = [
    "critical", "severe", "declining", "at risk", "at-risk", "failing",
    "failed", "missed", "urgent", "immediate", "significant drop",
    "significant decline", "major", "blocker", "blocked", "stalled",
    "no activity", "overdue", "behind schedule", "derailed", "p0", "p1",
    "outage", "incident", "escalated", "escalation", "churn", "churned",
    "lost", "cancelled", "canceled",
]

SEVERITY_2_MARKERS = [
    "watch", "flagged", "below target", "below plan", "warning",
    "concern", "risk", "risky", "slipping", "delayed", "behind",
    "unresolved", "deferred", "open question", "unclear", "pending",
    "not on track", "amber", "yellow", "slow", "slowing",
]

# ── WBR section headers to extract from ──────────────────────────────────────

WBR_EXTRACT_SECTIONS = [
    "anomal", "risk", "decision", "flag", "concern", "alert",
    "watch", "action required", "requires attention", "key finding",
    "highlight", "lowlight", "below target", "missed",
]

# ── Meeting Intelligence section headers ──────────────────────────────────────

MEETING_EXTRACT_SECTIONS = [
    "decision", "open item", "blocker", "unresolved", "deferred",
    "follow-up", "follow up", "action item", "owner", "next step",
    "outstanding", "pending", "unclear",
]

# ── Pipeline section headers ──────────────────────────────────────────────────

PIPELINE_EXTRACT_SECTIONS = [
    "risk", "stall", "stalled", "coverage", "gap", "action",
    "leadership", "forecast risk", "revenue risk", "at risk",
    "no activity", "deal risk", "concern", "flag",
]

# ── Initiative section headers ────────────────────────────────────────────────

INITIATIVE_EXTRACT_SECTIONS = [
    "drift", "blocked", "misalign", "strategic", "gap", "risk",
    "off-strategy", "off strategy", "behind", "delayed", "concern",
    "contradiction", "hidden", "leadership question",
]

# ── Deferral language (Meeting Intelligence) ──────────────────────────────────

DEFERRAL_MARKERS = [
    "deferred", "tabled", "not resolved", "again", "third", "fourth",
    "consecutive", "recurring", "repeated", "still open", "still unresolved",
    "came up again", "raised again", "continuing",
]

# ── Time reference patterns ───────────────────────────────────────────────────

TIME_REFERENCE_PATTERNS = [
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b",
    r"\b\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?\b",
    r"\b(?:this week|next week|this month|end of (?:week|month|quarter))\b",
    r"\b(?:q[1-4])\s*(?:close|deadline|end|target)?\b",
    r"\b(?:by|before|due|deadline)[:\s]+[a-z]+\s+\d{1,2}\b",
    r"\b\d{1,2}\s+days?\b",
    r"\b(?:june|july|august|september|october|november|december)\s+\d{1,2}\b",
    r"\bmonday|tuesday|wednesday|thursday|friday\b",
    r"\beow\b|\beom\b|\beoq\b",
]

# ── Output ranking by company type ────────────────────────────────────────────
# Determines display order of findings within each output bucket.
# Does not affect convergence scores.

THEME_RANK = {
    "Enterprise / B2B": [
        "enterprise_readiness",
        "go_to_market",
        "execution_risk",
        "customer_retention",
        "pricing_strategy",
        "capacity_constraints",
        "organizational_alignment",
        "strategic_drift",
        "product_reliability",
        "hiring_talent",
    ],
    "Consumer": [
        "customer_retention",
        "product_reliability",
        "go_to_market",
        "pricing_strategy",
        "execution_risk",
        "capacity_constraints",
        "organizational_alignment",
        "strategic_drift",
        "hiring_talent",
        "enterprise_readiness",
    ],
    "Mixed": [
        "customer_retention",
        "go_to_market",
        "enterprise_readiness",
        "execution_risk",
        "product_reliability",
        "pricing_strategy",
        "capacity_constraints",
        "organizational_alignment",
        "strategic_drift",
        "hiring_talent",
    ],
    "Other": [
        # Default: raw score order only (no reranking)
    ],
}
