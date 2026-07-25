# Investment Memo: {{ candidate.name }}

**Website:** {{ candidate.website or "N/A" }}
**Sector:** AI / Developer Tools
**Date Generated:** {{ date_generated }}

---

## Executive Summary

{{ analysis.executive_summary }}

## Investment Recommendation

**{{ analysis.recommendation }}**

**Confidence:** {{ analysis.confidence }}
**Investment Score:** {{ analysis.score }} / 100

| Dimension | Score |
|-----------|-------|
| Team | {{ analysis.score_breakdown.get("team", "N/A") }} |
| Product Fit | {{ analysis.score_breakdown.get("product_fit", "N/A") }} |
| Traction | {{ analysis.score_breakdown.get("traction", "N/A") }} |
| Risk (inverse) | {{ analysis.score_breakdown.get("risk", "N/A") }} |

---

## Company Snapshot

{% if candidate.extra %}
{% if candidate.extra.founded %}- **Founded:** {{ candidate.extra.founded }}{% endif %}
{% if candidate.extra.batch %}- **YC Batch:** {{ candidate.extra.batch }}{% endif %}
{% if candidate.extra.team_size %}- **Team Size:** {{ candidate.extra.team_size }}{% endif %}
{% endif %}
- **Source:** {{ candidate.source }}
{% if candidate.source_url %}- **Source URL:** {{ candidate.source_url }}{% endif %}

**Description:** {{ candidate.description }}

**Founders:** {{ candidate.founders or "Not available from sourced data" }}

---

## Product

{{ analysis.product }}

---

## Team

{{ analysis.team }}

---

## Market

{{ analysis.market }}

---

## Traction Signals

{{ analysis.traction_signals }}

{% if candidate.traction_signal %}
_From sourced data: {{ candidate.traction_signal.type }} — {{ candidate.traction_signal.detail }}_
{% endif %}

---

## Risks & Open Questions

{% for risk in analysis.risks %}
- {{ risk }}
{% endfor %}

---

## Thesis Alignment

{{ analysis.thesis_alignment }}

---

## What Would Change My Mind?

{% for item in analysis.change_my_mind %}
1. {{ item }}
{% endfor %}

---

## Sources

{% if candidate.source_url %}- [Source listing]({{ candidate.source_url }}){% endif %}
{% for url in analysis.sources %}
{% if url != candidate.source_url %}- {{ url }}{% endif %}
{% endfor %}
