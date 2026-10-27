
"""
Phase 4: Hacker News collector.
Fetches public stories from the Hacker News API
and saves them to the existing social_posts table.
"""

import requests
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

from config.settings import DATABASE_URL

BASE_URL = "https://hacker-news.firebaseio.com/v0"
engine = create_engine(DATABASE_URL)


def fetch_posts(limit: int = 20) -> list[dict]:
    """Fetch recent Hacker News stories."""

    limit = max(1, min(limit, 50))
    posts = []

    try:
        response = requests.get(
            f"{BASE_URL}/topstories.json",
            timeout=20,
        )
        response.raise_for_status()
        story_ids = response.json()[:limit]

        for story_id in story_ids:
            try:
                item_response = requests.get(
                    f"{BASE_URL}/item/{story_id}.json",
                    timeout=15,
                )
                item_response.raise_for_status()
                item = item_response.json()

                if not item or item.get("type") != "story":
                    continue

                if item.get("deleted") or item.get("dead"):
                    continue

                created_utc = datetime.fromtimestamp(
                    item["time"], tz=timezone.utc
                ).replace(tzinfo=None) if item.get("time") else None

                posts.append({
                    "post_id": str(item["id"]),
                    "title": item.get("title") or "Untitled",
                    "body": item.get("text") or "",
                    "score": item.get("score", 0),
                    "num_comments": item.get("descendants", 0),
                    "url": item.get("url") or
                           f"https://news.ycombinator.com/item?id={item['id']}",
                    "created_utc": created_utc,
                })

            except (requests.RequestException, ValueError, KeyError) as exc:
                print(f"Skipping story {story_id}: {exc}")

    except (requests.RequestException, ValueError) as exc:
        print(f"Hacker News API request failed: {exc}")
        return []

    print(f"Hacker News returned {len(posts)} stories.")
    return posts


def save_posts(posts: list[dict]) -> int:
    """Save stories into social_posts; skip duplicate IDs."""

    if not posts:
        print("No Hacker News stories to save.")
        return 0

    inserted = 0

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                SELECT id
                FROM public.sources
                WHERE name = 'hackernews'
            """)
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Hacker News source is missing from the sources table."
            )

        source_id = row[0]

        for post in posts:
            result = connection.execute(
                text("""
                    INSERT INTO public.social_posts (
                        source_id,
                        external_id,
                        subreddit,
                        title,
                        body,
                        score,
                        num_comments,
                        url,
                        created_utc
                    )
                    VALUES (
                        :source_id,
                        :external_id,
                        :subreddit,
                        :title,
                        :body,
                        :score,
                        :num_comments,
                        :url,
                        :created_utc
                    )
                    ON CONFLICT (source_id, external_id)
                    DO NOTHING
                """),
                {
                    "source_id": source_id,
                    "external_id": post["post_id"],
                    "subreddit": "hackernews",
                    "title": post["title"],
                    "body": post["body"],
                    "score": post["score"],
                    "num_comments": post["num_comments"],
                    "url": post["url"],
                    "created_utc": post["created_utc"],
                },
            )

            if result.rowcount == 1:
                inserted += 1

    print(f"Inserted {inserted} new Hacker News stories.")
    return inserted


if __name__ == "__main__":
    posts = fetch_posts(limit=20)
    save_posts(posts)
