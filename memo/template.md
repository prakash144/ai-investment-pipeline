# {{ candidate.name }}

{% if candidate.website %}_Website: {{ candidate.website }}_{% endif %}

---

## Team

{{ analysis.team }}

## Product

{{ analysis.product }}

## Market

{{ analysis.market }}

## Risks

{% for risk in analysis.risks %}
- {{ risk }}
{% endfor %}

## Score

**{{ analysis.score }} / 100**

| Dimension | Score |
|-----------|-------|
| Team | {{ analysis.score_breakdown.get("team", "N/A") }} |
| Product Fit | {{ analysis.score_breakdown.get("product_fit", "N/A") }} |
| Traction | {{ analysis.score_breakdown.get("traction", "N/A") }} |
| Risk (inverse) | {{ analysis.score_breakdown.get("risk", "N/A") }} |

## Call

**{{ analysis.recommendation }}**

## Change my mind

{% for item in analysis.change_my_mind %}
- {{ item }}
{% endfor %}

{% if analysis.sources or candidate.source_url %}
## Sources

{% if candidate.source_url %}- [Source listing]({{ candidate.source_url }}){% endif %}
{% for url in analysis.sources %}
{% if url != candidate.source_url %}- {{ url }}{% endif %}
{% endfor %}
{% endif %}
