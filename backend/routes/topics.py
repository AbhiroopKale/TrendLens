
"""
Phase 11: GET /topics endpoint.
Returns discovered topics stored in PostgreSQL.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/")
def list_topics(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the latest discovered topics."""

    query = text("""
        SELECT
            id,
            run_id,
            keywords,
            created_at
        FROM topics
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "topics": [dict(row) for row in rows],
    }
