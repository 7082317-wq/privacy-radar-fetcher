import feedparser
from supabase import create_client
from deep_translator import GoogleTranslator
import os
import re

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


feeds = [

    # =========================
    # AI Companies
    # =========================

    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Meta", "https://about.fb.com/news/feed/"),
    ("Anthropic", "https://www.anthropic.com/news/rss.xml"),
    ("Google", "https://blog.google/rss/"),
    ("DeepMind", "https://deepmind.google/discover/blog/rss.xml"),

    # =========================
    # AI / Tech Media
    # =========================

    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("Ars Technica AI", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Wired AI", "https://www.wired.com/feed/tag/ai/latest/rss"),

    # =========================
    # DPA / Governance
    # =========================

    ("EDPB", "https://www.edpb.europa.eu/news/rss_en"),
    ("ICO", "https://ico.org.uk/about-the-ico/media-centre/rss-feeds/"),
    ("CNIL", "https://www.cnil.fr/en/rss.xml"),
    ("OPC Canada", "https://www.priv.gc.ca/rss/news_nouvelles.xml"),
    ("PDPC Singapore", "https://www.pdpc.gov.sg/rss-feed"),

    # =========================
    # Standards / Security
    # =========================

    ("NIST", "https://www.nist.gov/news-events/news/rss.xml"),
    ("CISA", "https://www.cisa.gov/news.xml"),

]

AI_CAPABILITY_SIGNALS = {

    # Agentic AI
    "agent": 25,
    "agentic": 35,
    "ai agent": 40,
    "multi-agent": 35,
    "autonomous": 35,
    "delegation": 35,
    "workflow": 20,
    "orchestration": 30,

    # Computer Use
    "computer use": 40,
    "computer-use": 40,
    "browser": 20,
    "tool use": 30,
    "screen": 20,
    "operator": 20,
    "automation": 20,

    # Memory / Profiling
    "memory": 30,
    "persistent": 20,
    "personalization": 20,
    "profiling": 25,

    # Wearables / Ambient
    "wearable": 30,
    "glasses": 30,
    "ambient": 40,
    "camera": 15,
    "voice": 15,
    "real-time": 15,
    "always-on": 35,

    # Multimodal / Inference
    "multimodal": 30,
    "inference": 25,
    "emotion": 20,
    "behavior": 20,
    "tracking": 20,

    # Governance / Privacy
    "privacy": 15,
    "data protection": 20,
    "consent": 20,
    "transparency": 15,
    "controller": 20,
    "personal data": 20,

    # Security / AI Risk
    "ai risk": 20,
    "security": 15,
    "cybersecurity": 15,
    "surveillance": 25,
}

PRIVACY_IMPLICATION_MAPPING = {

    "agent": "위임된 개인정보 처리 가능성",
    "agentic": "자율적 개인정보 처리 가능성",
    "computer use": "서비스 간 데이터 접근 가능성",
    "browser": "브라우저 기반 개인정보 접근 가능성",
    "memory": "지속적 프로파일링 가능성",
    "persistent": "장기적 이용자 추적 가능성",
    "wearable": "상시 데이터 수집 가능성",
    "camera": "주변인 데이터 수집 가능성",
    "ambient": "비가시적 환경 정보 수집 가능성",
    "voice": "지속적 음성 수집 가능성",
    "screen": "화면 정보 노출 가능성",
    "delegation": "처리주체 불명확 가능성",
    "autonomous": "이용자 통제가능성 감소",
    "tracking": "행태정보 수집 가능성",
    "multimodal": "다중센서 기반 정보 결합 가능성",
    "profiling": "자동화된 프로파일링 가능성",
    "surveillance": "감시 가능성 증가",
}

for source_name, rss_url in feeds:

    print(f"\nChecking feed: {source_name}")

    try:
        feed = feedparser.parse(rss_url)

    except Exception as e:
        print(f"Feed parse failed: {e}")
        continue

    for entry in feed.entries[:10]:

        try:

            title = entry.title if "title" in entry else ""
            raw_summary = entry.summary if "summary" in entry else ""
            url = entry.link if "link" in entry else ""

            # HTML 제거
            summary = re.sub(r'<[^>]+>', '', raw_summary)
            summary = summary.strip()

            text = (title + " " + summary).lower()

            relevance_score = 0
            capability_tags = []
            privacy_implications = set()

            # capability scoring
            for keyword, score in AI_CAPABILITY_SIGNALS.items():

                if keyword in text:

                    relevance_score += score
                    capability_tags.append(keyword)

                    if keyword in PRIVACY_IMPLICATION_MAPPING:
                        privacy_implications.add(
                            PRIVACY_IMPLICATION_MAPPING[keyword]
                        )

            novelty_score = min(relevance_score, 100)

            # relevance threshold
            if relevance_score < 30:
                print(f"Skipped (low relevance): {title}")
                continue

            # duplicate check
            existing = (
                supabase
                .table("issues")
                .select("id")
                .eq("url", url)
                .execute()
            )

            if existing.data:
                print(f"Already exists: {title}")
                continue

            # 번역
            try:
                translated_title = GoogleTranslator(source='auto', target='ko').translate(title)

            except:
                translated_title = title

            try:
                translated_summary = translator.translate(
                    summary[:1000],
                    dest='ko'
                ).text

            except:
                translated_summary = summary[:1000]

            # insert
            supabase.table("issues").insert({

                "title": translated_title,
                "summary": translated_summary,

                "original_title": title,
                "original_summary": summary[:1000],

                "source": source_name,
                "url": url,

                "category": "Emerging AI Capability",

                "capability_tags": capability_tags,
                "privacy_implications": list(privacy_implications),

                "novelty_score": novelty_score,
                "relevance_score": relevance_score

            }).execute()

            print(f"Inserted: {translated_title}")

        except Exception as e:

            print(f"Error processing entry: {e}")
