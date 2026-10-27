# TrendLens — Web & Social Media Analytics Platform

Final-year B.Tech project. Collects news + social media text, runs NLP
(sentiment, topic modeling, keyword extraction), detects emerging trends
using velocity/burst/cross-source/sentiment-momentum signals, and serves
results through a FastAPI backend + Streamlit dashboard.

## Status: full skeleton, Phase 1 only is runnable

Every file for all 15 phases exists, but only Phase 1 (project setup /
DB connection) is real, working code. Every other file is a clearly
marked placeholder — it defines function signatures, docstrings, and
`TODO` comments, and raises `NotImplementedError` if called. Nothing
fakes results.

## File map (which file belongs to which phase)

| Phase | Files |
|---|---|
| 1 — Setup | `config/settings.py`, `requirements.txt`, `.env.example`, `scripts/test_db_connection.py` |
| 2 — DB schema | `database/schema.sql` (this one is complete, real SQL) |
| 3 — News API | `data_collection/news_api.py` |
| 4 — Reddit | `data_collection/reddit.py` |
| 5 — GDELT | `data_collection/gdelt.py` |
| 6 — Preprocessing | `preprocessing/cleaner.py`, `preprocessing/ner.py` |
| 7 — Sentiment | `analysis/sentiment.py` |
| 8 — Keywords | `analysis/keywords.py` |
| 9 — Topics | `analysis/topics.py` |
| 10 — Trend detection | `analysis/trends.py` |
| 11 — Backend | `backend/main.py`, `backend/routes/*.py`, `backend/services/db.py`, `backend/database/models.py` |
| 12 — Dashboard | `dashboard/app.py` |
| 13 — Integration | `orchestration/run_pipeline.py` |
| 14 — Testing | `tests/*.py` |
| 15 — Deployment | `docs/deployment.md` |

## Phase 1 setup (do this first — everything else depends on it)

1. Install Python 3.10+.
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install Phase 1 dependencies (the rest in `requirements.txt` aren't
   needed until their phase — install incrementally so you know what
   each package is for):
   ```
   pip install python-dotenv psycopg2-binary SQLAlchemy
   ```
4. Install PostgreSQL locally (or ask me about a free hosted option).
5. Create the database and user:
   ```sql
   CREATE DATABASE trendlens;
   CREATE USER trendlens_user WITH PASSWORD 'change_me';
   GRANT ALL PRIVILEGES ON DATABASE trendlens TO trendlens_user;
   ```
6. Copy `.env.example` to `.env` and fill in your real DB password.
7. Test the connection:
   ```
   python scripts/test_db_connection.py
   ```
   You should see `✅ Connected successfully.`
8. Once that works, run the Phase 2 schema:
   ```
   psql -U trendlens_user -d trendlens -f database/schema.sql
   ```

From here we go phase by phase, replacing each `NotImplementedError`
with real code — tell me when you're ready for Phase 3.
