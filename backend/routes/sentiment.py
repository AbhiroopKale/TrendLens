
"""
Phase 11: GET /sentiment endpoint.
Returns sentiment analysis results stored in PostgreSQL.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/")
def list_sentiment(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return the latest sentiment results."""
    limit = int(getattr(limit, "default", limit))

    query = text("""
        SELECT
            id,
            content_type,
            content_id,
            compound,
            pos,
            neu,
            neg,
            label,
            analyzed_at
        FROM sentiment_results
        ORDER BY analyzed_at DESC, id DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "sentiment": [dict(row) for row in rows],
    }
