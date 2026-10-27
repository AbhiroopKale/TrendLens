
"""
Phase 9: LDA topic modeling.
Groups documents by their word patterns.
"""

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer


def train_lda(documents: list[str], num_topics: int = 5):
    """
    Train an LDA model on a collection of documents.

    Returns:
        (model, topic_keywords)
        topic_keywords contains a list of important words per topic.
    """
    if num_topics < 1:
        raise ValueError("num_topics must be at least 1")

    if not documents or not any(
        doc and doc.strip() for doc in documents
    ):
        raise ValueError("Provide at least one non-empty document")

    vectorizer = CountVectorizer(
        stop_words="english",
        max_features=5000
    )

    try:
        document_term_matrix = vectorizer.fit_transform(documents)
    except ValueError as exc:
        raise ValueError(
            "Documents contain no usable words for topic modeling"
        ) from exc

    if document_term_matrix.shape[1] == 0:
        raise ValueError("No usable words found in documents")

    model = LatentDirichletAllocation(
        n_components=num_topics,
        random_state=42,
        max_iter=10,
        learning_method="batch"
    )

    model.fit(document_term_matrix)

    terms = vectorizer.get_feature_names_out()
    topic_keywords = []

    for topic in model.components_:
        top_indices = topic.argsort()[-10:][::-1]
        topic_keywords.append([
            terms[index] for index in top_indices
        ])

    # Keep the vectorizer attached to the model so assign_topics()
    # can transform new documents using the same vocabulary.
    model.trendlens_vectorizer = vectorizer

    return model, topic_keywords


def assign_topics(model, documents: list[str]) -> list[int]:
    """
    Assign each document to its dominant topic index.
    """
    if not documents:
        return []

    vectorizer = getattr(model, "trendlens_vectorizer", None)

    if vectorizer is None:
        raise ValueError(
            "Model vectorizer is missing. Use train_lda() first."
        )

    valid_indices = [
        i for i, doc in enumerate(documents)
        if doc and doc.strip()
    ]

    assignments = [-1] * len(documents)

    if not valid_indices:
        return assignments

    valid_documents = [documents[i] for i in valid_indices]
    document_term_matrix = vectorizer.transform(valid_documents)
    topic_distributions = model.transform(document_term_matrix)

    for row_index, original_index in enumerate(valid_indices):
        assignments[original_index] = int(
            topic_distributions[row_index].argmax()
        )

    return assignments
