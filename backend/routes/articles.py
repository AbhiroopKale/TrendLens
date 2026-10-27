
"""
Phase 11: GET /articles endpoint.
Returns articles stored in PostgreSQL.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/")
def list_articles(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the latest articles from the database."""
    limit = int(getattr(limit, "default", limit))
    query = text("""
        SELECT
            a.id,
            s.name AS source,
            a.title,
            a.content,
            a.category,
            a.url,
            a.published_at,
            a.created_at
        FROM articles a
        JOIN sources s ON s.id = a.source_id
        ORDER BY a.created_at DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "articles": [dict(row) for row in rows],
    }
