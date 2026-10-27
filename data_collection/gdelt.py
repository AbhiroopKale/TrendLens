"""
TrendLens: GDELT 2.0 Global News Collector.
Fetches real-time worldwide news from GDELT Doc API 2.0.
Respects fair-use rate limits with backoff and graceful error handling.
"""

import time
from datetime import datetime
import requests
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_gdelt_articles(query: str = "sourcelang:eng", max_records: int = 50) -> list[dict]:
    """
    Fetch articles from GDELT Doc API 2.0.
    Handles rate-limiting (429) with backoff.
    """
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": max(5, min(max_records, 150)),
        "format": "json",
        "timespan": "12h",
    }

    articles = []

    for attempt in range(3):
        try:
            response = requests.get(
                GDELT_DOC_URL,
                params=params,
                headers=DEFAULT_HEADERS,
                timeout=25,
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    items = data.get("articles", [])
                    for item in items:
                        url = item.get("url")
                        if not url:
                            continue

                        title = item.get("title") or "Untitled"
                        domain = item.get("domain") or item.get("sourcecommonname") or "GDELT"
                        source_country = item.get("sourcecountry") or "GLOBAL"

                        # Parse seendate (e.g., 20261021T180000Z)
                        pub_date = None
                        raw_date = item.get("seendate")
                        if raw_date:
                            try:
                                pub_date = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ")
                            except (ValueError, TypeError):
                                pub_date = None

                        articles.append({
                            "title": title,
                            "url": url,
                            "source": domain,
                            "domain": domain,
                            "country": source_country,
                            "category": "world",
                            "published_at": pub_date,
                            "description": f"[{domain} / {source_country}] {title}",
                        })

                    print(f"GDELT returned {len(articles)} worldwide articles.")
                    return articles

                except Exception as json_err:
                    print(f"GDELT JSON parsing error: {json_err}")
                    return []

            elif response.status_code == 429:
                wait_secs = 6 * (attempt + 1)
                print(f"GDELT rate-limited (429). Backing off for {wait_secs}s (attempt {attempt + 1}/3)...")
                time.sleep(wait_secs)
                continue
            else:
                print(f"GDELT returned status {response.status_code}: {response.text[:150]}")
                return []

        except requests.RequestException as exc:
            print(f"GDELT connection error: {exc}")
            time.sleep(4)

    return articles


def save_gdelt_articles(articles: list[dict]) -> int:
    """Save fetched GDELT articles into the PostgreSQL `articles` table."""
    if not articles:
        return 0

    inserted = 0

    with engine.begin() as connection:
        row = connection.execute(
            text("SELECT id FROM sources WHERE name = 'gdelt'")
        ).fetchone()

        if row is None:
            # Insert gdelt into sources if it somehow doesn't exist
            res = connection.execute(
                text("INSERT INTO sources (name, type) VALUES ('gdelt', 'news') RETURNING id")
            )
            source_id = res.scalar_one()
        else:
            source_id = row[0]

        for art in articles:
            url = art.get("url")
            if not url:
                continue

            result = connection.execute(
                text("""
                    INSERT INTO articles (
                        source_id, external_id, title, content,
                        category, url, published_at
                    )
                    VALUES (
                        :source_id, :external_id, :title, :content,
                        :category, :url, :published_at
                    )
                    ON CONFLICT (source_id, external_id) DO NOTHING
                """),
                {
                    "source_id": source_id,
                    "external_id": url,
                    "title": art.get("title") or "Untitled",
                    "content": art.get("description"),
                    "category": art.get("category") or "world",
                    "url": url,
                    "published_at": art.get("published_at"),
                },
            )
            inserted += max(result.rowcount, 0)

    print(f"Inserted {inserted} new GDELT articles into PostgreSQL.")
    return inserted


if __name__ == "__main__":
    arts = fetch_gdelt_articles(max_records=20)
    save_gdelt_articles(arts)
