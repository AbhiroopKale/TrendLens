
"""
TrendLens: GET /trends and GET /trends/{topic} endpoints.
Returns the latest observation for each keyword and its score history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.db import get_db

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/")
def list_trends(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the latest active observations for each keyword, ranked by trend score."""
    limit = int(getattr(limit, "default", limit))

    query = text("""
        WITH latest_active_snapshot AS (
            SELECT MAX(computed_at) AS max_computed_at
            FROM trend_results
            WHERE mention_count > 0
        )
        SELECT
            t.id,
            t.topic_or_keyword,
            t.window_start,
            t.window_end,
            t.mention_count,
            t.velocity_score,
            t.burst_score,
            t.source_count,
            t.sentiment_delta,
            t.trend_score,
            t.computed_at,
            COALESCE(
                (
                    SELECT a.category 
                    FROM articles a 
                    WHERE (a.title ILIKE '%' || t.topic_or_keyword || '%' OR a.content ILIKE '%' || t.topic_or_keyword || '%')
                      AND a.category IS NOT NULL
                    ORDER BY a.published_at DESC NULLS LAST
                    LIMIT 1
                ),
                'world'
            ) AS category
        FROM trend_results t
        JOIN latest_active_snapshot las ON t.computed_at = las.max_computed_at
        WHERE t.mention_count > 0
        ORDER BY t.trend_score DESC NULLS LAST, t.mention_count DESC, t.id DESC
        LIMIT :limit
    """)

    rows = db.execute(query, {"limit": limit}).mappings().all()

    # Fallback to general deduplication if no rows matched the active snapshot
    if not rows:
        fallback_query = text("""
            WITH latest_trends AS (
                SELECT
                    id,
                    topic_or_keyword,
                    window_start,
                    window_end,
                    mention_count,
                    velocity_score,
                    burst_score,
                    source_count,
                    sentiment_delta,
                    trend_score,
                    computed_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY LOWER(TRIM(topic_or_keyword))
                        ORDER BY computed_at DESC, id DESC
                    ) AS row_num
                FROM trend_results
            )
            SELECT
                id,
                topic_or_keyword,
                window_start,
                window_end,
                mention_count,
                velocity_score,
                burst_score,
                source_count,
                sentiment_delta,
                trend_score,
                computed_at
            FROM latest_trends
            WHERE row_num = 1
            ORDER BY trend_score DESC NULLS LAST, computed_at DESC
            LIMIT :limit
        """)
        rows = db.execute(fallback_query, {"limit": limit}).mappings().all()

    return {
        "count": len(rows),
        "trends": [dict(row) for row in rows],
    }


@router.get("/{topic}")
def get_trend_detail(
    topic: str,
    db: Session = Depends(get_db),
):
    """Return all observations for a keyword, newest first, plus matching content."""

    query = text("""
        SELECT
            id,
            topic_or_keyword,
            window_start,
            window_end,
            mention_count,
            velocity_score,
            burst_score,
            source_count,
            sentiment_delta,
            trend_score,
            computed_at
        FROM trend_results
        WHERE LOWER(TRIM(topic_or_keyword)) = LOWER(TRIM(:topic))
        ORDER BY computed_at DESC, id DESC
    """)

    rows = db.execute(query, {"topic": topic}).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No trend results found for '{topic}'",
        )

    # Fetch matching news articles and social posts for contextual intelligence
    pattern = f"%{topic.strip()}%"
    articles_query = text("""
        SELECT a.id, a.title, a.content, a.url, a.published_at, s.name AS source_name
        FROM articles a
        JOIN sources s ON s.id = a.source_id
        WHERE a.title ILIKE :pattern OR a.content ILIKE :pattern
        ORDER BY a.published_at DESC NULLS LAST, a.id DESC
        LIMIT 6
    """)
    articles = db.execute(articles_query, {"pattern": pattern}).mappings().all()

    posts_query = text("""
        SELECT p.id, p.title, p.body AS content, p.url, p.score, p.num_comments,
               p.created_utc, s.name AS source_name
        FROM social_posts p
        JOIN sources s ON s.id = p.source_id
        WHERE p.title ILIKE :pattern OR p.body ILIKE :pattern
        ORDER BY p.score DESC NULLS LAST, p.created_utc DESC NULLS LAST, p.id DESC
        LIMIT 6
    """)
    posts = db.execute(posts_query, {"pattern": pattern}).mappings().all()

    return {
        "topic": rows[0]["topic_or_keyword"],
        "count": len(rows),
        "latest": dict(rows[0]),
        "results": [dict(row) for row in rows],
        "articles": [dict(a) for a in articles],
        "posts": [dict(p) for p in posts],
    }
