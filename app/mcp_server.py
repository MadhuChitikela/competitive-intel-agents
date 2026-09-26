from fastmcp import FastMCP
from pydantic import Field
from datetime import datetime, timezone
import uuid
import hashlib

mcp = FastMCP(name="competitive-intel")

# In-memory stores — swap for a real DB or P1's SQLite later
_NEWS_STORE: list[dict] = []
_PRICING_STORE: dict[str, dict] = {}
_JOBS_STORE: list[dict] = []
_SIGNALS_SEEN: set[str] = set()


def _signal_id(*parts: str) -> str:
    """Deterministic ID so the same signal doesn't duplicate across runs."""
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Tool 1 — News
# ---------------------------------------------------------------------------
@mcp.tool()
def fetch_competitor_news(
    company: str = Field(description="Company name to fetch news for"),
    days: int = Field(default=7, description="Look back N days"),
) -> list[dict]:
    """Fetch recent news signals for a competitor.

    Returns a list of signals with id, title, source, url, published_at.
    Stub — swap the body for NewsAPI / GNews / a real crawler later.
    """
    now = datetime.now(timezone.utc).isoformat()
    raw_signals = [
        (f"{company} launches new AI product line", "TechCrunch",
         f"https://example.com/{company.lower()}/ai-launch"),
        (f"{company} raises Series B funding", "Economic Times",
         f"https://example.com/{company.lower()}/series-b"),
        (f"{company} partners with major cloud provider", "Mint",
         f"https://example.com/{company.lower()}/cloud-partnership"),
    ]
    out = []
    for title, source, url in raw_signals:
        sid = _signal_id(company, title)
        if sid in _SIGNALS_SEEN:
            continue
        _SIGNALS_SEEN.add(sid)
        signal = {
            "id": sid,
            "company": company,
            "title": title,
            "source": source,
            "url": url,
            "published_at": now,
        }
        out.append(signal)
        _NEWS_STORE.append(signal)
    return out


# ---------------------------------------------------------------------------
# Tool 2 — Pricing
# ---------------------------------------------------------------------------
@mcp.tool()
def scrape_pricing_page(
    url: str = Field(description="URL of the competitor's pricing page"),
) -> dict:
    """Extract pricing tiers from a competitor's pricing page.

    Returns {"url", "tiers": [{"name", "price", "features"}], "scraped_at"}.
    Stub — swap for Playwright / Firecrawl later.
    """
    tiers = [
        {"name": "Starter", "price": "$29/mo",
         "features": ["1 user", "Basic support"]},
        {"name": "Pro", "price": "$99/mo",
         "features": ["5 users", "Priority support", "API access"]},
        {"name": "Enterprise", "price": "Custom",
         "features": ["Unlimited users", "SSO", "SLA"]},
    ]
    result = {
        "url": url,
        "tiers": tiers,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
    _PRICING_STORE[url] = result
    return result


# ---------------------------------------------------------------------------
# Tool 3 — Job postings
# ---------------------------------------------------------------------------
@mcp.tool()
def check_job_postings(
    company: str = Field(description="Company name to check hiring signals for"),
) -> list[dict]:
    """Detect hiring signals from a company's job postings.

    Returns list of {"role", "team", "signal"} — hiring in a new team
    is a strong signal of strategic direction.
    """
    roles = [
        ("Senior ML Engineer", "AI Platform",
         "Investing in AI infrastructure"),
        ("Enterprise Account Executive", "Sales",
         "Moving upmarket to enterprise deals"),
        ("Head of Partnerships", "Business Development",
         "Building channel/partner ecosystem"),
    ]
    out = []
    for role, team, signal in roles:
        sid = _signal_id(company, role)
        job = {
            "id": sid,
            "company": company,
            "role": role,
            "team": team,
            "signal": signal,
            "source": "LinkedIn (stub)",
        }
        out.append(job)
        _JOBS_STORE.append(job)
    return out


# ---------------------------------------------------------------------------
# Tool 4 — Threat scoring
# ---------------------------------------------------------------------------
@mcp.tool()
def score_threat(
    competitor: str = Field(description="Competitor name"),
    signal: str = Field(description="The signal text to score"),
    current_offer: str = Field(
        default="AI-powered CRM for SMBs",
        description="Your own product offering for context",
    ),
) -> dict:
    """Score a competitive signal from 0-100 on how threatening it is.

    Deterministic stub scoring — swap for an LLM call for nuanced scoring.
    Higher score = more threat to your business.
    """
    text = signal.lower()
    score = 20  # baseline
    reasons = ["baseline signal"]

    if "ai" in text or "ml" in text:
        score += 30
        reasons.append("direct overlap with AI offering")
    if "enterprise" in text or "upmarket" in text:
        score += 20
        reasons.append("moving upmarket")
    if "funding" in text or "raises" in text:
        score += 15
        reasons.append("capital to expand")
    if "partnership" in text or "ecosystem" in text:
        score += 10
        reasons.append("channel expansion")

    score = min(score, 100)
    level = "high" if score >= 70 else "medium" if score >= 40 else "low"

    return {
        "competitor": competitor,
        "signal": signal,
        "score": score,
        "level": level,
        "reasons": reasons,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Tool 5 — Self-audit (THE CENTERPIECE)
# ---------------------------------------------------------------------------
DEFAULT_RUBRIC = {
    "structure": "Has exec summary, threats, opportunities, recommendations",
    "evidence": "Every claim cites a specific signal or source",
    "actionable": "Recommendations are concrete, not vague",
    "concise": "Under 400 words, no filler",
}


@mcp.tool()
def audit_brief(
    brief_text: str = Field(description="The intelligence brief to grade"),
    rubric: dict = Field(
        default_factory=lambda: DEFAULT_RUBRIC,
        description="Rubric criteria -> description",
    ),
) -> dict:
    """Self-audit a competitive intelligence brief against a rubric.

    Returns {"score": 0-1, "passed": bool, "issues": [...], "criteria": {...}}.
    Deterministic heuristic stub — swap for LLM-as-judge later, OR better:
    route this through P1's judge() for a full LLM grade.
    """
    text = brief_text.lower()
    issues: list[str] = []
    criteria: dict[str, dict] = {}

    # Structure check
    needed = ["executive summary", "threat", "opportunit", "recommend"]
    missing = [n for n in needed if n not in text]
    structure_ok = len(missing) == 0
    criteria["structure"] = {
        "passed": structure_ok,
        "missing": missing,
    }
    if not structure_ok:
        issues.append(f"Missing sections: {missing}")

    # Evidence check — count citations or urls
    evidence_count = text.count("http") + text.count("source:")
    evidence_ok = evidence_count >= 3
    criteria["evidence"] = {
        "passed": evidence_ok,
        "count": evidence_count,
    }
    if not evidence_ok:
        issues.append(f"Only {evidence_count} citations — need 3+")

    # Actionable check — imperative verbs
    action_verbs = ["hire", "launch", "build", "prioritize", "respond",
                    "monitor", "partner", "increase", "reduce", "ship"]
    action_count = sum(text.count(v) for v in action_verbs)
    actionable_ok = action_count >= 2
    criteria["actionable"] = {
        "passed": actionable_ok,
        "count": action_count,
    }
    if not actionable_ok:
        issues.append(f"Only {action_count} action verbs — need 2+")

    # Conciseness — word count
    word_count = len(brief_text.split())
    concise_ok = word_count <= 400
    criteria["concise"] = {
        "passed": concise_ok,
        "word_count": word_count,
    }
    if not concise_ok:
        issues.append(f"Brief is {word_count} words — over 400 limit")

    # Weighted score
    weights = {"structure": 0.35, "evidence": 0.30,
               "actionable": 0.25, "concise": 0.10}
    score = sum(weights[k] for k, v in criteria.items() if v["passed"])

    return {
        "score": round(score, 3),
        "passed": score >= 0.8,
        "issues": issues,
        "criteria": criteria,
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }
