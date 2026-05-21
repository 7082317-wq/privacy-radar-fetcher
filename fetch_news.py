import feedparser
from supabase import create_client
import os
import re

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

feeds = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Meta", "https://about.fb.com/news/feed/"),
    ("Anthropic", "https://www.anthropic.com/news/rss.xml"),
    ("Google", "https://blog.google/rss/"),
]

AI_CAPABILITY_SIGNALS = {
    "agent": 25,
    "agentic": 30,
    "computer use": 35,
    "browser": 15,
    "tool use": 30,
    "autonomous": 30,
    "workflow": 15,
    "assistant": 15,
    "memory": 25,
    "persistent": 20,
    "wearable": 25,
    "glasses": 25,
    "camera": 15,
    "voice": 15,
    "ambient": 35,
    "multimodal": 25,
    "real-time": 15,
    "screen": 20,
    "delegation": 35,
    "operator": 20,
    "automation": 20,
}

PRIVACY_IMPLICATION_MAPPING = {
    "agent": "delegated processing",
    "computer use": "cross-service data access",
    "memory": "persistent profiling",
    "wearable": "always-on collection",
    "camera": "bystander data collection",
    "ambient": "invisible environmental sensing",
    "voice": "continuous audio capture",
    "screen": "screen content exposure",
    "delegation": "unclear controller boundaries",
    "autonomous": "reduced user controllability",
}

for source_name, rss_url in feeds:

    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:10]:

        title = entry.title if "title" in entry else ""
        raw_summary = entry.summary if "summary" in entry else ""
        url = entry.link if "link" in entry else ""

        summary = re.sub(r'<[^>]+>', '', raw_summary)
        summary = summary.strip()

        text = (title + " " + summary).lower()

        relevance_score = 0
        capability_tags = []
        privacy_implications = set()

        for keyword, score in AI_CAPABILITY_SIGNALS.items():

            if keyword in text:

                relevance_score += score
                capability_tags.append(keyword)

                if keyword in PRIVACY_IMPLICATION_MAPPING:
                    privacy_implications.add(
                        PRIVACY_IMPLICATION_MAPPING[keyword]
                    )

        novelty_score = min(relevance_score, 100)

        # threshold filtering
        if relevance_score < 30:
            continue

        existing = (
            supabase
            .table("issues")
            .select("id")
            .eq("url", url)
            .execute()
        )

        if not existing.data:

            supabase.table("issues").insert({
                "title": title,
                "summary": summary[:1000],
                "source": source_name,
                "url": url,
                "category": "Emerging AI Capability",
                "capability_tags": capability_tags,
                "privacy_implications": list(privacy_implications),
                "novelty_score": novelty_score,
                "relevance_score": relevance_score
            }).execute()

            print(f"Inserted: {title}")
