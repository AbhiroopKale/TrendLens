"""
Phase 11: SQLAlchemy ORM models mirroring database/schema.sql.
These map directly to the tables created in Phase 2 — kept in sync manually
since the schema is simple enough for a college project.
"""
from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=False)
    external_id = Column(String(500), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text)
    category = Column(String(100))
    url = Column(Text)
    published_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)


class SocialPost(Base):
    __tablename__ = "social_posts"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=False)
    external_id = Column(String(100), nullable=False)
    subreddit = Column(String(100))
    title = Column(Text)
    body = Column(Text)
    score = Column(Integer)
    num_comments = Column(Integer)
    url = Column(Text)
    created_utc = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)


class TrendResult(Base):
    __tablename__ = "trend_results"
    id = Column(Integer, primary_key=True)
    topic_or_keyword = Column(String(200), nullable=False)
    window_start = Column(TIMESTAMP, nullable=False)
    window_end = Column(TIMESTAMP, nullable=False)
    velocity_score = Column(Float)
    burst_score = Column(Float)
    source_count = Column(Integer)
    sentiment_delta = Column(Float)
    trend_score = Column(Float, nullable=False)
    computed_at = Column(TIMESTAMP)

# TODO (Phase 11): add Source, SentimentResult, Topic, TopicAssignment,
# Keyword models the same way, matching database/schema.sql.
