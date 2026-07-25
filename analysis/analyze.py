import json
import os
import threading
from pathlib import Path

from openai import OpenAI

from analysis.schema import Analysis
from config import get_llm_api_key, get_llm_api_base


class NoApiKeyError(Exception):
    pass


ANALYSIS_SYSTEM_PROMPT = """You are a VC investment analyst evaluating early-stage startups. Your analysis must be grounded entirely in the provided candidate data.

## ANTI-HALLUCINATION RULES (these are mandatory)

1. ONLY use information explicitly present in the candidate data below.
2. Do NOT invent or assume founder names, market sizes, competitor names, traction numbers, GitHub stars, funding amounts, or any other facts not present in the provided data.
3. If a data point is marked as unavailable or absent, state "Not available from sourced data" — never fabricate it.
4. When scoring a dimension with incomplete data, score conservatively based on available signals. Do NOT default to zero — use partial credit where the available info is promising.
5. Every claim in your analysis must be traceable to a specific field in the candidate data. Include source URLs where applicable.

## Investment Thesis Weights

- Team (30): technical founder, prior relevant exit/experience, research background
- Product fit for SMB (25): clear SMB buyer, plain-language use case
- Traction (25): HN activity, recent launch, funding signal in last 12-18mo
- Risk (20, inverse score): fewer risks = higher score

## Scoring Guidance for Missing Data

- If founder info is absent but the product/description suggests domain expertise: score Team 10-15 (not zero), note the gap
- If traction data is absent: score Traction 5-10 (not zero), note the gap
- Low confidence when multiple key data points are missing
- High confidence when most data is available, consistent, and verifiable

## Recommendation

- "Take a meeting" = strong on Team + Traction, clearly in-thesis. Score typically 70+
- "Watch" = in-thesis but missing one key signal. Score typically 45-69
- "Pass" = out of thesis or disqualifying risk. Score typically below 45

Return valid JSON only with these fields:
- executive_summary (str): 5-6 line summary covering company, product, market, team, and call
- team (str): founder background assessment — only what's in the data
- product (str): what they build in plain language — no marketing fluff
- market (str): market assessment — only cite competitors/markets if mentioned in data
- traction_signals (str): all traction evidence found in the data
- risks (list[str]): 2-4 key risks grounded in available data
- thesis_alignment (str): why this company fits or doesn't fit the stated thesis
- score (int): 0-100 weighted final score
- score_breakdown (dict): keys team, product_fit, traction, risk (0-100 each)
- confidence (str): "High", "Medium", or "Low"
- recommendation (str): "Pass", "Watch", or "Take a meeting"
- change_my_mind (list[str]): 2-3 specific things that would change the call
- sources (list[str]): URLs referenced in your analysis"""


def build_prompt(candidate: dict, thesis: str) -> str:
    sections = [f"# Investment Thesis\n\n{thesis}\n"]
    sections.append("# Candidate Data\n")

    sections.append(f"**Name:** {candidate.get('name', 'Unknown')}")
    sections.append(f"**Website:** {candidate.get('website', 'Not available')}")
    sections.append(f"**Description:** {candidate.get('description', 'Not available')}")
    sections.append(f"**Source:** {candidate.get('source', 'Unknown')}")
    sections.append(f"**Source URL:** {candidate.get('source_url', 'Not available')}")

    founders = candidate.get("founders")
    if founders:
        sections.append(f"**Founders:** {founders}")
    else:
        sections.append("**Founders:** NOT AVAILABLE — no founder information was found from sourced data")

    traction = candidate.get("traction_signal")
    if traction:
        sections.append(f"**Traction Signal:** {traction.get('type', '')} — {traction.get('detail', '')}")
        sections.append(f"**Traction Source:** {traction.get('source_url', 'Not available')}")
    else:
        sections.append("**Traction Signal:** NOT AVAILABLE — no traction signal was found from sourced data")

    extra = candidate.get("extra")
    if extra:
        sections.append("\n**Enriched Data:**")
        if isinstance(extra, dict):
            for key, value in extra.items():
                if value:
                    sections.append(f"- {key}: {value}")

    return "\n".join(sections)


_log_lock = threading.Lock()


def log_prompt_call(candidate_slug: str, prompt: str, response_text: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    log_path = Path("logs/prompts.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "candidate_slug": candidate_slug,
        "prompt": prompt,
        "response": response_text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
    }
    with _log_lock:
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


def get_or_analyze(candidate: dict, thesis: str, cache_dir: Path = Path("data/analysis"), llm_client=None) -> Analysis:
    slug = candidate["slug"]
    cache_path = cache_dir / f"{slug}.json"

    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        return Analysis(**data)

    api_key = get_llm_api_key()
    if not api_key:
        raise NoApiKeyError(f"no LLM_API_KEY set and no cached analysis for '{candidate.get('name', slug)}'")

    if llm_client is None:
        llm_client = OpenAI(api_key=api_key, base_url=get_llm_api_base())

    prompt = build_prompt(candidate, thesis)

    response = llm_client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=2000,
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError(f"Empty response from LLM for '{slug}'")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON for '{slug}': {e}")

    analysis = Analysis(**parsed)

    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        f.write(analysis.model_dump_json(indent=2))

    model = response.model
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost = estimate_cost(model, input_tokens, output_tokens)
    log_prompt_call(slug, prompt, content, model, input_tokens, output_tokens, cost)

    return analysis


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "gpt-4-turbo": (10.00, 30.00),
        "gpt-3.5-turbo": (0.50, 1.50),
    }
    rate = rates.get(model, (1.00, 2.00))
    return (input_tokens / 1_000_000 * rate[0]) + (output_tokens / 1_000_000 * rate[1])
