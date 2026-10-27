"""
Phase 12: Streamlit dashboard entrypoint.
Run with: streamlit run dashboard/app.py
STATUS: page layout only — not yet wired to the FastAPI backend or real data.
"""
import streamlit as st

st.set_page_config(page_title="TrendLens", layout="wide")
st.title("TrendLens — Web & Social Media Analytics")

st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Articles", "—")
col2.metric("Total Social Posts", "—")
col3.metric("Number of Topics", "—")
col4.metric("Emerging Trends", "—")
# TODO (Phase 12): pull real counts from GET /articles, /posts, /topics, /trends

st.subheader("Sentiment")
st.write("TODO: positive/neutral/negative breakdown + sentiment-over-time chart (Plotly)")

st.subheader("Topics")
st.write("TODO: topic distribution + top keywords per topic")

st.subheader("Keywords")
st.write("TODO: top keywords ranked by TF-IDF score")

st.subheader("🔥 Emerging Trends")
st.write("TODO: trend score, growth %, contributing sources, sentiment momentum — "
         "and WHY each topic was flagged, not just the score")

st.subheader("News vs Reddit Comparison")
st.write("TODO: side-by-side sentiment and topic-volume comparison")

# TODO (Phase 12): add sidebar filters — date range, source, topic, sentiment
