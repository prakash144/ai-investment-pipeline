YC_BATCHES = {
    "W25": [
        {
            "name": "Resend",
            "website": "https://resend.com",
            "description": "Email API for developers to send transactional emails",
            "batch": "W25",
        },
        {
            "name": "Sieve",
            "website": "https://sievedata.com",
            "description": "Video AI platform for developers to build and deploy video applications",
            "batch": "W25",
        },
        {
            "name": "MindsDB",
            "website": "https://mindsdb.com",
            "description": "Open-source platform for building AI-powered applications with databases",
            "batch": "W25",
        },
        {
            "name": "Helicone",
            "website": "https://helicone.ai",
            "description": "Observability platform for LLM applications",
            "batch": "W25",
        },
        {
            "name": "Langfuse",
            "website": "https://langfuse.com",
            "description": "Open-source observability and evaluation platform for LLM applications",
            "batch": "W25",
        },
        {
            "name": "Porter",
            "website": "https://porter.run",
            "description": "Platform for deploying and managing web applications on AWS",
            "batch": "W25",
        },
        {
            "name": "Kraftful",
            "website": "https://kraftful.com",
            "description": "AI-powered product research assistant that analyzes user feedback",
            "batch": "W25",
        },
        {
            "name": "Tally",
            "website": "https://tally.so",
            "description": "No-code form builder with AI-powered form creation",
            "batch": "W25",
        },
        {
            "name": "Screenpipe",
            "website": "https://screenpi.pe",
            "description": "AI-powered screen recording and analysis for developers",
            "batch": "W25",
        },
        {
            "name": "Bland AI",
            "website": "https://bland.ai",
            "description": "AI phone call agents for businesses to automate customer interactions",
            "batch": "W25",
        },
        {
            "name": "Dover",
            "website": "https://dover.com",
            "description": "AI-powered recruiting automation platform for SMBs",
            "batch": "W25",
        },
        {
            "name": "MutableAI",
            "website": "https://mutable.ai",
            "description": "AI-powered codebase documentation and refactoring tool",
            "batch": "W25",
        },
        {
            "name": "Tempo Labs",
            "website": "https://tempo.sh",
            "description": "AI-powered UI design tool that generates production code",
            "batch": "W25",
        },
        {
            "name": "Typo",
            "website": None,
            "description": "AI writing assistant focused on professional communication",
            "batch": "W25",
        },
        {
            "name": "Reworkd",
            "website": "https://reworkd.ai",
            "description": "AI agent platform for automating browser-based workflows",
            "batch": "W25",
        },
    ]
}


def fetch_yc_candidates(batch: str = "W25", limit: int = 20) -> list[dict]:
    if batch not in YC_BATCHES:
        return []
    companies = YC_BATCHES[batch]
    results = []
    for company in companies[:limit]:
        results.append(
            {
                "name": company["name"],
                "website": company.get("website"),
                "description": company["description"],
                "batch": company["batch"],
                "source": "yc",
            }
        )
    return results
