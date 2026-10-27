
"""
Phase 7: VADER sentiment analysis.
Returns compound, positive, neutral, negative scores and a label.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> dict:
    """
    Returns:
        {
            "compound": float,
            "pos": float,
            "neu": float,
            "neg": float,
            "label": str
        }

    Labels:
        compound >= 0.05  -> positive
        compound <= -0.05 -> negative
        otherwise         -> neutral
    """

    if not text or not text.strip():
        return {
            "compound": 0.0,
            "pos": 0.0,
            "neu": 1.0,
            "neg": 0.0,
            "label": "neutral",
        }

    scores = analyzer.polarity_scores(text)

    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "compound": float(compound),
        "pos": float(scores["pos"]),
        "neu": float(scores["neu"]),
        "neg": float(scores["neg"]),
        "label": label,
    }
