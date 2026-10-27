
"""
Phase 6: Text preprocessing.
Lowercase, remove URLs/mentions/noise, tokenize,
remove stopwords while preserving negation, and lemmatize.
"""

import re
import spacy
from nltk.corpus import stopwords

try:
    nlp = spacy.load("en_core_web_sm")
except OSError as exc:
    raise RuntimeError(
        "spaCy English model missing. Run: "
        "python -m spacy download en_core_web_sm"
    ) from exc

try:
    STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    import nltk
    nltk.download("stopwords", quiet=True)
    STOP_WORDS = set(stopwords.words("english"))

# Preserve these words because they affect sentiment.
NEGATIONS = {"no", "not", "nor", "never", "n't"}
STOP_WORDS -= NEGATIONS


def clean_text(raw_text: str) -> str:
    """Clean text for sentiment, keywords and topic modeling."""

    if not raw_text:
        return ""

    text = str(raw_text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"[^a-z\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    doc = nlp(text)
    tokens = []

    for token in doc:
        if token.is_space or token.is_punct:
            continue
        if token.is_stop and token.text not in NEGATIONS:
            continue
        if token.pos_ in ("VERB", "AUX", "PRON", "SCONJ", "CCONJ", "DET", "PUNCT", "SYM", "SPACE", "ADV"):
            continue

        lemma = token.lemma_.strip()
        if lemma and lemma.isalpha() and len(lemma) > 1:
            tokens.append(lemma)

    return " ".join(tokens)
