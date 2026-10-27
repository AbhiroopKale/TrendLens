
"""
TrendLens: end-to-end collection and analysis pipeline.

Run from the project root:
    python -m orchestration.run_pipeline

Trend history is retained between runs. Historical comparisons become
more useful after several successful runs have accumulated.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from uuid import uuid4

from sqlalchemy import text

from urllib.parse import urlparse
from backend.services.db import engine
from data_collection.news_api import fetch_top_headlines, save_articles
from data_collection.gdelt import fetch_gdelt_articles, save_gdelt_articles
from data_collection.hacker_news import fetch_posts, save_posts
from preprocessing.cleaner import clean_text
from preprocessing.ner import extract_entities
from analysis.sentiment import analyze_sentiment
from analysis.keywords import extract_keywords
from analysis.topics import train_lda
from analysis.trends import (
    compute_velocity,
    compute_burst_score,
    compute_source_validation,
    compute_sentiment_momentum,
    compute_trend_score,
)


# World news filler and generic non-trend terms.
NOISY_TERMS = {
    "quot", "amp", "nbsp", "wrt", "dd", "ll", "ve", "http", "https",
    "www", "html", "href", "said", "says", "say", "saying", "told", "thing", "today",
    "yesterday", "tomorrow", "new", "news", "report", "reports", "reported", "reporting",
    "article", "update", "updates", "video", "image", "click", "read",
    "official", "officials", "statement", "authorities", "minister",
    "run", "use", "make", "build", "exceed", "usd", "trillion", "billion",
    "percent", "center", "datum", "data", "people", "man", "woman", "person",
    "year", "years", "time", "day", "days", "week", "month", "like", "good",
    "way", "work", "post", "comment", "point", "case", "fact",
    "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "monday",
}

# Normalize common world news entity variants to unified names
ENTITY_ALIASES = {
    "trump": "donald trump",
    "biden": "joe biden",
    "netanyahu": "benjamin netanyahu",
    "musk": "elon musk",
    "harris": "kamala harris",
    "putin": "vladimir putin",
    "zelensky": "volodymyr zelenskyy",
    "zelenskyy": "volodymyr zelenskyy",
    "modi": "narendra modi",
    "starmer": "keir starmer",
}


def valid_keyword(term: str) -> bool:
    """Reject markup remnants, generic verbs/fillers, and low-information candidate terms."""
    term = re.sub(r"\s+", " ", (term or "").lower()).strip()
    if not term or term in NOISY_TERMS:
        return False
    if len(term) < 3 or term.isdigit():
        return False
    words = term.split()
    if any(w in ("quot", "amp", "nbsp", "usd", "exceed", "run", "use", "wrt", "http", "https") for w in words):
        return False
    if all(w in NOISY_TERMS for w in words):
        return False
    return bool(re.search(r"[a-z]", term))


def extract_outlet(url: str, default_name: str = "news") -> str:
    """Extract publisher domain / news outlet from URL for distinct outlet counting."""
    if not url:
        return default_name
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        domain = domain.split(":")[0]
        return domain if domain else default_name
    except Exception:
        return default_name


def collect_data():
    """Collect world news across GNews categories, GDELT worldwide, and Hacker News."""
    print("\nStep 1: Collecting data from worldwide sources")

    # 1. Multi-category GNews (World, Business, Tech, Nation, Sports across US, GB, IN)
    try:
        articles = fetch_top_headlines(
            categories=["world", "nation", "business", "technology", "sports"],
            countries=["us", "gb", "in"],
            max_per_call=8,
        )
        save_articles(articles)
    except Exception as exc:
        print(f"GNews top-headlines skipped/error: {exc}")

    # 2. GDELT global news database (worldwide coverage, no API key needed)
    try:
        gdelt_articles = fetch_gdelt_articles(max_records=30)
        save_gdelt_articles(gdelt_articles)
    except Exception as exc:
        print(f"GDELT collection skipped/error: {exc}")

    # 3. Hacker News social discussions
    try:
        posts = fetch_posts(limit=20)
        save_posts(posts)
    except Exception as exc:
        print(f"Hacker News collection skipped/error: {exc}")


def load_documents():
    """Load saved articles and posts along with distinct publisher outlet and category."""
    with engine.connect() as connection:
        articles = connection.execute(text("""
            SELECT a.id, a.title, a.content, a.url, a.category, s.name AS source_type
            FROM articles a
            JOIN sources s ON s.id = a.source_id
        """)).mappings().all()

        posts = connection.execute(text("""
            SELECT p.id, p.title, p.body AS content, p.url, s.name AS source_type
            FROM social_posts p
            JOIN sources s ON s.id = p.source_id
        """)).mappings().all()

    documents = []
    for row in articles:
        outlet = extract_outlet(row["url"], row["source_type"])
        documents.append({
            "type": "article", "id": row["id"], "source": outlet,
            "category": row["category"] or "world",
            "text": f'{row["title"] or ""} {row["content"] or ""}'.strip(),
        })
    for row in posts:
        documents.append({
            "type": "post", "id": row["id"], "source": "Hacker News",
            "category": "technology",
            "text": f'{row["title"] or ""} {row["content"] or ""}'.strip(),
        })
    return documents


def run():
    run_id = uuid4().hex[:12]
    collect_data()

    print("\nLoading documents from PostgreSQL")
    documents = [d for d in load_documents() if d["text"].strip()]
    if not documents:
        print("No documents found. Pipeline stopped.")
        return
    print(f"Loaded {len(documents)} documents.")

    print("\nStep 2: Preprocessing and entity extraction")
    for doc in documents:
        doc["cleaned"] = clean_text(doc["text"])
        doc["entities"] = extract_entities(doc["text"])

    usable = [d for d in documents if d["cleaned"].strip()]
    if not usable:
        print("No usable text after preprocessing. Pipeline stopped.")
        return

    print("\nStep 3: Sentiment analysis")
    for doc in usable:
        doc["sentiment"] = analyze_sentiment(doc["text"])

    print("\nStep 4: TF-IDF keyword extraction & entity fusion")
    keyword_results = extract_keywords([d["cleaned"] for d in usable], top_n=10)
    for doc, keywords in zip(usable, keyword_results):
        kw_dict = {term: score for term, score in keywords if valid_keyword(term)}
        # Merge high-value Named Entities with alias normalization
        for ent in doc.get("entities", []):
            ent_text = ent["text"].lower().strip()
            if ent.get("label") in ("PERSON", "GPE", "ORG", "NORP", "EVENT") and valid_keyword(ent_text):
                norm_text = ENTITY_ALIASES.get(ent_text, ent_text)
                if norm_text not in kw_dict:
                    kw_dict[norm_text] = 0.5
        doc["keywords"] = list(kw_dict.items())

    print("\nStep 5: LDA topic modelling")
    model = None
    topic_keywords = []
    if len(usable) >= 2:
        try:
            model, topic_keywords = train_lda(
                [d["cleaned"] for d in usable],
                num_topics=min(5, len(usable)),
            )
            matrix = model.trendlens_vectorizer.transform(
                [d["cleaned"] for d in usable]
            )
            distributions = model.transform(matrix)
            for index, doc in enumerate(usable):
                doc["topic_id"] = int(distributions[index].argmax())
                doc["topic_weight"] = float(
                    distributions[index, doc["topic_id"]]
                )
        except ValueError as exc:
            print(f"Topic modelling skipped: {exc}")
            model = None
            topic_keywords = []

    print("\nStep 6: Saving analysis and calculating trends")
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)
    historical_start = now - timedelta(days=30)

    # Aggregate a term once per document. TF-IDF is used to select
    # candidate terms; distinct document count measures their prevalence.
    groups = defaultdict(list)
    for doc in usable:
        seen_terms = set()
        for term, tfidf_score in doc["keywords"]:
            if term in seen_terms:
                continue
            seen_terms.add(term)
            groups[term].append({
                "doc": doc,
                "score": tfidf_score,
            })

    # Require at least two distinct documents before treating a keyword
    # as a trend candidate. This reduces one-off keyword noise.
    groups = {
        term: items for term, items in groups.items()
        if len({item["doc"]["id"] for item in items}) >= 2
    }

    with engine.begin() as connection:
        # Rebuild current derived analysis, but KEEP trend_results history.
        connection.execute(text("DELETE FROM topic_assignments"))
        connection.execute(text("DELETE FROM topics"))
        connection.execute(text("DELETE FROM keywords"))
        connection.execute(text("DELETE FROM sentiment_results"))

        for doc in usable:
            s = doc["sentiment"]
            connection.execute(text("""
                INSERT INTO sentiment_results
                    (content_type, content_id, compound, pos, neu, neg, label)
                VALUES
                    (:content_type, :content_id, :compound, :pos, :neu, :neg, :label)
            """), {
                "content_type": doc["type"], "content_id": doc["id"],
                "compound": s["compound"], "pos": s["pos"],
                "neu": s["neu"], "neg": s["neg"], "label": s["label"],
            })

            for term, score in doc["keywords"]:
                connection.execute(text("""
                    INSERT INTO keywords (content_type, content_id, term, tfidf_score)
                    VALUES (:content_type, :content_id, :term, :score)
                """), {
                    "content_type": doc["type"], "content_id": doc["id"],
                    "term": term[:100], "score": score,
                })

        topic_ids = {}
        if model is not None:
            for index, words in enumerate(topic_keywords):
                result = connection.execute(text("""
                    INSERT INTO topics (run_id, keywords)
                    VALUES (:run_id, :keywords)
                    RETURNING id
                """), {
                    "run_id": run_id,
                    "keywords": ", ".join(w for w in words if valid_keyword(w)),
                })
                topic_ids[index] = result.scalar_one()

            for doc in usable:
                if "topic_id" not in doc:
                    continue
                connection.execute(text("""
                    INSERT INTO topic_assignments
                        (content_type, content_id, topic_id, weight)
                    VALUES (:content_type, :content_id, :topic_id, :weight)
                """), {
                    "content_type": doc["type"], "content_id": doc["id"],
                    "topic_id": topic_ids[doc["topic_id"]],
                    "weight": doc["topic_weight"],
                })

        saved_trends = 0
        for term, items in groups.items():
            # Distinct documents, not TF-IDF rows, are counted.
            members_by_id = {item["doc"]["id"]: item["doc"] for item in items}
            members = list(members_by_id.values())
            current_count = len(members)
            sources = {doc["source"] for doc in members}
            avg_sentiment = mean(doc["sentiment"]["compound"] for doc in members)
            entity_count = sum(len(doc["entities"]) for doc in members)
            entity_prominence = min(
                1.0, entity_count / max(1, current_count * 3)
            )

            # Historical observations are for this same term only.
            history = connection.execute(text("""
                SELECT mention_count, sentiment_delta
                FROM trend_results
                WHERE LOWER(TRIM(topic_or_keyword)) = LOWER(TRIM(:term))
                  AND computed_at >= :start
                  AND computed_at < :now
                  AND mention_count > 0
                ORDER BY computed_at DESC
                LIMIT 14
            """), {
                "term": term,
                "start": historical_start.replace(tzinfo=None),
                "now": now.replace(tzinfo=None),
            }).mappings().all()

            history_counts = [int(row["mention_count"]) for row in history]
            history_sentiments = [
                float(row["sentiment_delta"]) for row in history
            ]

            if history_counts:
                historical_avg = mean(history_counts)
                raw_velocity = compute_velocity(current_count, historical_avg)
                velocity_signal = max(0.0, raw_velocity)
                burst = compute_burst_score(current_count, history_counts)
                previous_sentiment = history_sentiments[0]
                sentiment_momentum = compute_sentiment_momentum(
                    previous_sentiment, avg_sentiment
                )
            else:
                # No baseline means no claim of growth or burst.
                raw_velocity = 0.0
                velocity_signal = 0.0
                burst = 0.0
                sentiment_momentum = 0.0

            source_validation = compute_source_validation(sources)
            score = compute_trend_score(
                velocity_signal,
                burst,
                source_validation,
                sentiment_momentum,
                entity_prominence,
            )

            connection.execute(text("""
                INSERT INTO trend_results (
                    topic_or_keyword, window_start, window_end,
                    velocity_score, burst_score, source_count,
                    sentiment_delta, trend_score, mention_count, computed_at
                )
                VALUES (
                    :term, :window_start, :window_end,
                    :velocity, :burst, :source_count,
                    :sentiment, :score, :mentions, :computed_at
                )
            """), {
                "term": term[:200],
                "window_start": window_start.replace(tzinfo=None),
                "window_end": now.replace(tzinfo=None),
                "velocity": raw_velocity,
                "burst": burst,
                "source_count": len(sources),
                "sentiment": avg_sentiment,
                "score": score,
                "mentions": current_count,
                "computed_at": now.replace(tzinfo=None),
            })
            saved_trends += 1

    print("\nPipeline completed successfully.")
    print(f"Documents processed: {len(usable)}")
    print(f"Sentiment records: {len(usable)}")
    print(f"Topic records: {len(topic_keywords) if model else 0}")
    print(f"Keyword trend observations saved: {saved_trends}")
    print("Historical trend observations were retained.")
    print(f"Run ID: {run_id}")


if __name__ == "__main__":
    run()
