
"""
Phase 3: GNews collector.
Fetches articles from GNews and saves them to PostgreSQL.
"""

import requests
from datetime import datetime
from sqlalchemy import create_engine, text

from config.settings import GNEWS_API_KEY, DATABASE_URL

GNEWS_API_URL = "https://gnews.io/api/v4/search"
engine = create_engine(DATABASE_URL)


def fetch_articles(query: str, page_size: int = 20) -> list[dict]:
    if not GNEWS_API_KEY:
        print("GNEWS_API_KEY is missing from .env")
        return []

    params = {
        "q": query,
        "lang": "en",
        "max": max(1, min(page_size, 100)),
        "apikey": GNEWS_API_KEY,
    }

    try:
        response = requests.get(
            GNEWS_API_URL,
            params=params,
            timeout=20,
        )

        if response.status_code != 200:
            print(f"GNews error ({response.status_code}): {response.text[:300]}")
            return []

        data = response.json()

    except requests.RequestException as exc:
        print(f"GNews connection error: {exc}")
        return []

    articles = []

    for item in data.get("articles", []):
        url = item.get("url")
        if not url:
            continue

        published_at = item.get("publishedAt")
        try:
            published_at = (
                datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                if published_at else None
            )
        except (ValueError, AttributeError):
            published_at = None

        source = item.get("source") or {}

        articles.append({
            "title": item.get("title") or "Untitled",
            "description": item.get("description"),
            "url": url,
            "source": source.get("name") or "GNews",
            "published_at": published_at,
        })

    print(f"GNews returned {len(articles)} articles.")
    return articles


GNEWS_TOP_HEADLINES_URL = "https://gnews.io/api/v4/top-headlines"


def fetch_top_headlines(
    categories: list[str] = None,
    countries: list[str] = None,
    max_per_call: int = 10,
) -> list[dict]:
    """
    Fetch top headlines across multiple categories and countries from GNews.
    Maintains a 1-second pause between calls to respect the free-tier rate limits.
    """
    if not GNEWS_API_KEY:
        print("GNEWS_API_KEY is missing from .env")
        return []

    import time

    categories = categories or [
        "world", "nation", "business", "technology",
        "entertainment", "sports", "science", "health",
    ]
    countries = countries or ["us", "gb", "in"]

    all_articles = []
    seen_urls = set()

    print(f"\nFetching top headlines across {len(categories)} categories & {len(countries)} countries...")

    for country in countries:
        for cat in categories:
            params = {
                "category": cat,
                "country": country,
                "lang": "en",
                "max": max(1, min(max_per_call, 10)),
                "apikey": GNEWS_API_KEY,
            }

            try:
                response = requests.get(
                    GNEWS_TOP_HEADLINES_URL,
                    params=params,
                    timeout=20,
                )

                if response.status_code == 200:
                    data = response.json()
                    cat_articles = data.get("articles", [])
                    new_count = 0
                    for item in cat_articles:
                        url = item.get("url")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)

                        published_at = item.get("publishedAt")
                        try:
                            published_at = (
                                datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                                if published_at else None
                            )
                        except (ValueError, AttributeError):
                            published_at = None

                        source_info = item.get("source") or {}
                        all_articles.append({
                            "title": item.get("title") or "Untitled",
                            "description": item.get("description"),
                            "url": url,
                            "source": source_info.get("name") or "GNews",
                            "category": cat,
                            "published_at": published_at,
                        })
                        new_count += 1

                elif response.status_code == 429:
                    print(f"GNews rate limit reached ({cat}/{country}): {response.text[:200]}")
                    break
                else:
                    print(f"GNews {cat}/{country} returned {response.status_code}")

            except requests.RequestException as exc:
                print(f"GNews connection error for {cat}/{country}: {exc}")

            # Sleep 1.1s to strictly respect the 1 request/second rule
            time.sleep(1.1)

    print(f"GNews top-headlines returned {len(all_articles)} unique articles.")
    return all_articles


def save_articles(articles: list[dict]) -> int:
    if not articles:
        print("No articles to save.")
        return 0

    inserted = 0

    with engine.begin() as connection:
        row = connection.execute(
            text("SELECT id FROM sources WHERE name = 'newsapi'")
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Database source 'newsapi' was not found. "
                "Check the sources table in pgAdmin."
            )

        source_id = row[0]

        for article in articles:
            url = article.get("url")
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
                    "title": article.get("title") or "Untitled",
                    "content": article.get("description"),
                    "category": article.get("category"),
                    "url": url,
                    "published_at": article.get("published_at"),
                },
            )

            inserted += max(result.rowcount, 0)

    print(f"Inserted {inserted} new articles into PostgreSQL.")
    return inserted


if __name__ == "__main__":
    articles = fetch_top_headlines(categories=["world", "business", "technology"], countries=["us", "gb"])
    save_articles(articles)
