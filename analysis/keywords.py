
"""TrendLens: clean TF-IDF keyword extraction."""

import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

CUSTOM_STOP_WORDS = {
    "quot", "amp", "nbsp", "ldquo", "rdquo", "apos", "ndash", "mdash",
    "href", "https", "http", "www", "html", "div", "span", "wrt",
    "dd", "ll", "ve", "don", "doesn", "isn", "aren", "didn", "wasn",
    "weren", "won", "wouldn", "couldn", "shouldn", "said", "says", "say",
    "run", "runs", "running", "use", "uses", "using", "used", "make", "makes",
    "making", "made", "build", "builds", "building", "built", "come", "comes",
    "coming", "came", "get", "gets", "getting", "got", "know", "knows",
    "think", "thinks", "take", "takes", "taking", "took", "want", "wants",
    "like", "look", "looks", "help", "helps", "need", "needs", "good", "great",
    "new", "news", "report", "reports", "article", "update", "updates",
    "thing", "things", "time", "times", "year", "years", "day", "days",
    "today", "yesterday", "tomorrow", "people", "way", "ways", "work", "works",
    "post", "posts", "comment", "comments", "read", "click", "view",
    "point", "points", "case", "cases", "world", "fact", "percent",
    "usd", "trillion", "billion", "million", "exceed", "exceeds", "exceeded",
    "center", "datum",
    "official", "officials", "minister", "authorities", "statement", "told",
    "according", "reported", "reporting", "spokesman", "spokesperson",
    "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "monday",
    "man", "woman", "person", "public",
}

STOP_WORDS = list(ENGLISH_STOP_WORDS.union(CUSTOM_STOP_WORDS))


def clean_keyword_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"&(?:amp|quot|nbsp|lt|gt|#\d+|#x[0-9a-f]+);?", " ", text)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords(documents: list[str], top_n: int = 10) -> list[list[tuple]]:
    if not documents or top_n <= 0:
        return [[] for _ in documents]

    cleaned = [clean_keyword_text(doc) for doc in documents]
    valid_indices = [i for i, doc in enumerate(cleaned) if doc]
    results = [[] for _ in documents]
    if not valid_indices:
        return results

    valid_docs = [cleaned[i] for i in valid_indices]
    vectorizer = TfidfVectorizer(
        stop_words=STOP_WORDS,
        max_features=5000,
        ngram_range=(1, 2),
        min_df=1,
        token_pattern=r"(?u)\b[a-z][a-z0-9-]{1,}\b",
        sublinear_tf=True,
    )

    try:
        matrix = vectorizer.fit_transform(valid_docs)
    except ValueError:
        return results

    terms = vectorizer.get_feature_names_out()
    for row_index, original_index in enumerate(valid_indices):
        row = matrix.getrow(row_index)
        pairs = sorted(
            ((terms[i], float(score)) for i, score in zip(row.indices, row.data)),
            key=lambda item: item[1],
            reverse=True,
        )
        results[original_index] = pairs[:top_n]

    return results
