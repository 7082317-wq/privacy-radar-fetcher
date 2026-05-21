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
]

for source_name, rss_url in feeds:
    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:5]:

        title = entry.title
        raw_summary = entry.summary if "summary" in entry else ""
        summary = re.sub(r'<[^>]+>', '', raw_summary)
        summary = summary.strip()
        url = entry.link

        existing = supabase.table("issues").select("id").eq("url", url).execute()

        if not existing.data:

            supabase.table("issues").insert({
                "title": title,
                "summary": summary[:500],
                "source": source_name,
                "url": url,
                "category": "Emerging AI",
                "capability_tags": ["needs-analysis"],
                "privacy_implications": ["pending-review"],
                "novelty_score": 70,
                "relevance_score": 75
            }).execute()

            print(f"Inserted: {title}")
