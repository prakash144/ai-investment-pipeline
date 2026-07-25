import json
import os
from pathlib import Path

from openai import OpenAI

from analysis.schema import Analysis
from config import get_llm_api_key


class NoApiKeyError(Exception):
    pass


ANALYSIS_SYSTEM_PROMPT = """You are a VC investment analyst evaluating early-stage startups.
Given a candidate company and an investment thesis, produce a structured analysis.

Score each dimension (0-100 scale) and provide a weighted final score.

Thesis-based scoring weights:
- Team (30): technical founder, prior relevant exit/experience, research background
- Product fit for SMB (25): clear SMB buyer, plain-language use case
- Traction (25): HN activity, recent launch, funding signal in last 12-18mo
- Risk (20, inverse score): fewer risks = higher score

Recommendation:
- "Take a meeting" = strong on Team + Traction, clearly in-thesis
- "Watch" = in-thesis but missing one key signal
- "Pass" = out of thesis or disqualifying risk

Return valid JSON only with these fields:
- team (str): founder background assessment
- product (str): what they build in plain language
- market (str): market size, growth, timing, competitors
- risks (list[str]): 2-4 key risks
- score (int): 0-100 weighted score
- score_breakdown (dict): keys team, product_fit, traction, risk (int values)
- recommendation (str): "Pass", "Watch", or "Take a meeting"
- change_my_mind (list[str]): 2-3 things that would change the call
- sources (list[str]): URLs referenced in your analysis"""


def build_prompt(candidate: dict, thesis: str) -> str:
    sections = [f"# Investment Thesis\n\n{thesis}\n"]
    sections.append("# Candidate\n")

    for field in ["name", "website", "description", "founders", "traction_signal"]:
        value = candidate.get(field)
        if value is None:
            if field == "founders":
                sections.append("- founders: No founder information was found for this company")
            elif field == "traction_signal":
                sections.append("- traction_signal: No traction signal was found for this company")
            else:
                sections.append(f"- {field}: Not available")
        else:
            sections.append(f"- {field}: {value}")

    sections.append(f"\n# Source\n{candidate.get('source_url', 'Not available')}")
    return "\n".join(sections)


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
        llm_client = OpenAI(api_key=api_key)

    prompt = build_prompt(candidate, thesis)

    response = llm_client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
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
