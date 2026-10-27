"""
Phase 11: FastAPI backend entrypoint.
Run with: uvicorn backend.main:app --reload
STATUS: app boots, but each route currently raises NotImplementedError
until its phase is built.
"""
from fastapi import FastAPI
from backend.routes import articles, posts, sentiment, topics, keywords, trends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TrendLens API")

app.include_router(articles.router)
app.include_router(posts.router)
app.include_router(sentiment.router)
app.include_router(topics.router)
app.include_router(keywords.router)
app.include_router(trends.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "TrendLens API is running"}
