-- TrendLens database schema (Phase 2)
-- Raw data tables (articles, social_posts) are kept separate from derived
-- analysis tables (sentiment_results, topics, keywords, trend_results).

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,   -- 'newsapi', 'reddit', 'gdelt'
    type VARCHAR(20) NOT NULL           -- 'news' | 'social' | 'event'
);

CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    external_id VARCHAR(500) NOT NULL,  -- article URL, used for dedup
    title TEXT NOT NULL,
    content TEXT,
    category VARCHAR(100),
    url TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source_id, external_id)
);
CREATE INDEX idx_articles_published_at ON articles(published_at);

CREATE TABLE social_posts (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    external_id VARCHAR(100) NOT NULL,  -- Reddit post ID, used for dedup
    subreddit VARCHAR(100),
    title TEXT,
    body TEXT,
    score INTEGER,
    num_comments INTEGER,
    url TEXT,
    created_utc TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source_id, external_id)
);
CREATE INDEX idx_social_posts_created_utc ON social_posts(created_utc);

CREATE TABLE sentiment_results (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(10) NOT NULL,  -- 'article' | 'post'
    content_id INTEGER NOT NULL,
    compound FLOAT NOT NULL,
    pos FLOAT NOT NULL,
    neu FLOAT NOT NULL,
    neg FLOAT NOT NULL,
    label VARCHAR(10) NOT NULL,         -- 'positive' | 'neutral' | 'negative'
    analyzed_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sentiment_content ON sentiment_results(content_type, content_id);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,        -- identifies which LDA run produced this
    keywords TEXT NOT NULL,             -- comma-separated top words
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE topic_assignments (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(10) NOT NULL,
    content_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    weight FLOAT NOT NULL
);
CREATE INDEX idx_topic_assignments_content ON topic_assignments(content_type, content_id);

CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(10) NOT NULL,
    content_id INTEGER NOT NULL,
    term VARCHAR(100) NOT NULL,
    tfidf_score FLOAT NOT NULL,
    extracted_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_keywords_content ON keywords(content_type, content_id);

CREATE TABLE trend_results (
    id SERIAL PRIMARY KEY,
    topic_or_keyword VARCHAR(200) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    velocity_score FLOAT,
    burst_score FLOAT,
    source_count INTEGER,
    sentiment_delta FLOAT,
    trend_score FLOAT NOT NULL,
    computed_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_trend_results_score ON trend_results(trend_score DESC);

-- Seed the known sources
INSERT INTO sources (name, type) VALUES
    ('newsapi', 'news'),
    ('reddit', 'social'),
    ('gdelt', 'event');
