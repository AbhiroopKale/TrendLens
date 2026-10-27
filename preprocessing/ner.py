
"""
Phase 6: Named Entity Recognition using spaCy.
Extracts people, organizations, locations and other entities.
"""

import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError as exc:
    raise RuntimeError(
        "spaCy English model is missing. Run: "
        "python -m spacy download en_core_web_sm"
    ) from exc


def extract_entities(text: str) -> list[dict]:
    """
    Return entities as dictionaries:
    [{"text": "OpenAI", "label": "ORG"}, ...]
    """

    if not text or not text.strip():
        return []

    doc = nlp(text)

    return [
        {
            "text": entity.text,
            "label": entity.label_,
        }
        for entity in doc.ents
    ]
