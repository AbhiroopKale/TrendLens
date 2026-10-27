
"""
Phase 11: GET /keywords endpoint.
Returns extracted keywords stored in PostgreSQL.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("/")
def list_keywords(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return the most recently extracted keywords."""

    query = text("""
        SELECT
            k.id,
            k.content_type,
            k.content_id,
            k.term,
            k.tfidf_score,
            k.extracted_at
        FROM keywords k
        ORDER BY k.extracted_at DESC, k.id DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "keywords": [dict(row) for row in rows],
    }
