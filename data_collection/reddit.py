"""
Phase 4: Reddit collector (via PRAW).
Fetches posts from target subreddits into the `social_posts` table.
STATUS: placeholder.
"""
from config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

TARGET_SUBREDDITS = ["worldnews", "technology", "business"]


def fetch_posts(subreddit: str, limit: int = 50) -> list[dict]:
    """
    Fetch recent posts from a subreddit.
    Returns list of dicts: post_id, title, body, score, num_comments,
    created_utc, url.
    TODO (Phase 4): implement using praw.Reddit(...)
    """
    raise NotImplementedError("Implement in Phase 4")


def save_posts(posts: list[dict]) -> int:
    """
    Insert posts into `social_posts`, skipping duplicates on
    (source_id, external_id).
    TODO (Phase 4): implement using SQLAlchemy.
    """
    raise NotImplementedError("Implement in Phase 4")


if __name__ == "__main__":
    for sub in TARGET_SUBREDDITS:
        posts = fetch_posts(sub)
        inserted = save_posts(posts)
        print(f"r/{sub}: inserted {inserted} new posts")
