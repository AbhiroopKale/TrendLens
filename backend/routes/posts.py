
"""
Phase 11: GET /posts endpoint.
Returns social posts stored in PostgreSQL.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/")
def list_posts(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the latest social posts from the database."""
    limit = int(getattr(limit, "default", limit))

    query = text("""
        SELECT
            p.id,
            s.name AS source,
            p.external_id,
            p.subreddit,
            p.title,
            p.body,
            p.score,
            p.num_comments,
            p.url,
            p.created_utc,
            p.created_at
        FROM social_posts p
        JOIN sources s ON s.id = p.source_id
        ORDER BY p.created_at DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "posts": [dict(row) for row in rows],
    }
