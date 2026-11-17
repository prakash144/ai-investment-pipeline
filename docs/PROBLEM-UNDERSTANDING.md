# AI-Augmented Investment Pipeline (Take-Home)

---

# 1. What is this assignment?

This is **not just a coding assignment**.

The company wants to evaluate **how an engineer thinks**, **how they use AI**, **how they make technical decisions**, and **whether they can build a practical system with good judgment**.

Instead of building a huge application, we're expected to build a **small, focused, replayable pipeline** that helps Venture Capital (VC) partners evaluate startups faster.

---

# 2. The Real Business Problem

Imagine you are the **first engineer** at a small VC firm.

Currently partners spend around **10 hours every week** manually doing things like:

- Browsing Product Hunt
- Reading Hacker News
- Checking Y Combinator batches
- Looking at Twitter/X
- Reading Crunchbase

For every startup they find they manually answer questions like:

- What does this company do?
- Is the team strong?
- Is this market attractive?
- Is it growing?
- Should we spend time talking to them?

Most startups are rejected.

The goal is **not to replace investors.**

Instead, build an **AI-powered first screening system** that automatically performs the repetitive research and presents only the strongest companies.

Think of it as:

```
Internet
    │
    ▼
Collect Startups
    │
    ▼
Research Each Startup
    │
    ▼
Generate Investment Memo
    │
    ▼
VC Partner Makes Final Decision
```

---

# 3. What are we actually building?

The assignment defines a pipeline with **three stages**.

```
Input
   │
   ▼
Stage 1
Sourcing
   │
   ▼
Stage 2
Analysis
   │
   ▼
Stage 3
Recommendation
   │
   ▼
Investment Memo
```

Each stage should be independent.

---

# Stage 1 — Sourcing

## Goal

Find startup companies from public sources.

The input could be:

- Topic
- List of URLs
- YC Batch
- Product Hunt collection

Example input:

```
AI agents for SMBs
```

Our system should discover around

- 10–20 startups

For every startup collect basic information.

Example:

```json
{
  "name": "Cursor",
  "website": "https://cursor.com",
  "description": "...",
  "founders": "...",
  "traction": "GitHub stars increased..."
}
```

---

### Required fields

The assignment asks for:

- Startup name
- Website
- One-line description
- Founder/team signal
- At least one freshness/traction signal

Traction can be things like

- Product Hunt launch
- YC batch
- Funding
- GitHub activity
- Hacker News popularity
- Recent announcement

---

### Important note

They explicitly say:

> Pick one or two sources and go deep.

This means

❌ Don't scrape everything.

Better:

- Product Hunt + YC

or

- Hacker News + GitHub

than

10 shallow sources.

Good engineering judgment > More code.

---

# Stage 2 — Analysis

This is the heart of the assignment.

For every startup we must generate structured research.

The required sections are:

## Team

Questions:

- Who founded the company?
- Previous companies?
- Technical background?
- Exits?
- Research experience?

Example

```
Founder previously worked at OpenAI.

Strong AI engineering experience.

No previous startup exits.
```

---

## Product

Explain simply.

Not marketing language.

Instead answer

> What do they actually build?

Example

Instead of

> Revolutionary AI platform

Write

> AI agent that automates customer support for Shopify stores.

---

## Market

Think like an investor.

Questions:

- Is this a large market?
- Growing?
- Why now?
- Competitors?
- Market timing?

Example

```
Growing demand due to LLM adoption.

Competes with...

Large SMB automation market.
```

---

## Risks

Every startup has risks.

Examples

- Easy to copy
- No clear moat
- Depends on OpenAI pricing
- Small market
- Weak founder experience
- Regulatory concerns

Investors care as much about risks as opportunities.

---

## Score

Give every company a score.

Example

```
84 / 100
```

But...

The score must follow a defined investment thesis.

---

# Investment Thesis

This is one of the most important parts.

The assignment says:

> You define the thesis.

Example of a weak thesis

```
Good companies.
```

Impossible to score consistently.

Better:

> AI-native SaaS companies building autonomous workflow agents for SMBs with technical founders and early user traction.

Now every score can follow this framework.

Example scoring:

| Category | Weight |
|-----------|---------|
| Team | 30 |
| Market | 20 |
| Product | 20 |
| Traction | 20 |
| Risks | 10 |

Final Score = weighted sum.

Now scoring becomes explainable.

---

# Stage 3 — Recommendation

This stage converts research into an investment memo.

Every memo should end with one recommendation:

```
PASS
```

or

```
WATCH
```

or

```
TAKE A MEETING
```

Along with:

Why?

And

What would change your mind?

Example

```
Recommendation

WATCH

Reason

Excellent founders but no meaningful traction.

Would change mind if

- 100 paying customers
- Successful enterprise pilot
- Stronger product differentiation
```

---

# Final Output

For every startup:

```
Memo

Summary

Team

Product

Market

Risks

Score

Recommendation
```

This should be readable by a VC in under one minute.

---

# 4. Hidden Goal of the Assignment

This is where many candidates fail.

The assignment repeatedly mentions AI.

Not because they want ChatGPT-generated code.

They want to understand:

- How did you think?
- How did AI help?
- Where did AI fail?
- What decisions did you make?
- What did you change manually?

This contributes **40%** of the total score.

That is larger than code quality.

---

# Showing AI Workflow

The reviewers should clearly see:

Planning

↓

Architecture decisions

↓

Prompt iterations

↓

Failures

↓

Fixes

↓

Final implementation

Possible evidence:

```
docs/

planning.md

design-decisions.md

prompt-log.md

mistakes.md

tradeoffs.md

```

This should feel authentic—not something assembled afterward.

---

# 5. System Design Expectations

The assignment explicitly says

Don't overengineer.

Avoid:

❌ Kubernetes

❌ Complex frontend

❌ Vector database cluster

❌ Large distributed architecture

Instead build something like

```
CLI

↓

Source Collector

↓

Analyzer

↓

Memo Generator

↓

Markdown Output
```

Simple.

Replayable.

Maintainable.

---

# 6. Replayability

Reviewer should run

```bash
python main.py \
    --topic "AI agents for SMBs"
```

or

```bash
make run
```

Pipeline runs

↓

Outputs memos

↓

Done.

No manual work.

---

# 7. Traceability

The assignment specifically mentions:

> Claims should be traceable.

Meaning

Don't write

```
Company is growing fast.
```

Instead

```
Recent Product Hunt launch

GitHub: 3k stars

YC W25

Funding announced May 2025
```

Every important statement should point back to a public source.

---

# 8. Understanding the Rubric

## Process & AI Workflow (40%)

Most important.

Questions reviewers ask:

- Can I see how this was built?
- Were engineering decisions documented?
- Was AI used thoughtfully?
- Is the workflow honest?

---

## Output Quality (20%)

Can an investor actually use these memos?

Good:

- concise
- evidence-backed
- structured

Bad:

- generic LLM summaries

---

## Scoping & Judgment (20%)

Did we build the right amount?

Good:

- Product Hunt only
- High-quality analysis

Bad:

- 12 sources
- Poor analysis

---

## System Design (10%)

Code organization.

Example

```
src/

collectors/

analyzers/

prompts/

models/

writers/
```

Simple.

Modular.

Replayable.

---

## Code Quality (10%)

Readable.

Documented.

Small functions.

Reasonable testing.

No unnecessary abstraction.

---

# 9. Anti-Patterns to Avoid

The assignment explicitly warns against:

❌ Generic AI-written reflections

❌ Huge scraping systems

❌ Unsupported investment claims

❌ Broad investment thesis

❌ Hidden AI usage

❌ Overengineered infrastructure

---

# 10. What Does Success Look Like?

A VC partner should be able to:

- Run one command.
- Receive startup memos.
- Read one memo in under 60 seconds.
- Decide whether to spend time on the company.

A reviewer should be able to:

- Verify every important claim.
- Understand how the pipeline works.
- Understand how AI was used during development.
- Trust the engineering decisions.

---

# 11. Deliverables

The final submission should include:

- Source code repository
- README with setup instructions
- Replayable pipeline
- Generated startup memos (committed to the repo)
- Documentation showing planning, AI workflow, and design decisions
- ~5-minute walkthrough video demonstrating one startup end-to-end

---

# Key Takeaways

This assignment is primarily evaluating **engineering judgment**, not just implementation speed.

The strongest solution will:

- Focus on one clear investment thesis.
- Go deep on one or two high-quality startup sources.
- Keep the architecture simple and replayable.
- Produce concise, evidence-backed investment memos.
- Make AI usage transparent through authentic documentation.
- Demonstrate thoughtful trade-offs rather than unnecessary complexity.

In short:

> Build a practical AI-assisted investment analyst that a VC partner would actually use, while making your engineering process and AI collaboration visible and trustworthy.