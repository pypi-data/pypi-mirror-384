import re
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_text(text: str) -> str:
    """
    Preprocess a text string by normalizing its case and removing punctuation.

    This function converts all characters in the input text to lowercase
    and removes any punctuation marks, keeping only alphanumeric characters
    and whitespace.

    Args:
        text (str): The input text string to preprocess.

    Returns:
        str: A cleaned version of the text with lowercase characters
             and no punctuation.
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text


# def str_to_bool(s):
#     return {'true': True, 'false': False}[s.lower()]


def nlp_processor(msg: str, patterns: Any = None, threshold: float = 0.5) -> bool:
    """
    Process a message using TF-IDF vectorization and cosine similarity to
    determine whether it matches a given pattern (e.g., a fallback pattern).

    This function compares the input `msg` against one or more patterns
    by preprocessing the text (lowercasing, removing punctuation) and then
    computing cosine similarity between their TF-IDF representations.
    If the maximum similarity exceeds the given threshold, the function
    returns True, indicating a match.

    Args:
        msg (str): The input message to analyze.
        patterns (str or list[str], optional): The reference pattern(s) to compare against.
                                               Can be a single string or a list of strings.
                                               Defaults to None (will raise error if not provided).
        threshold (float, optional): Similarity threshold in the range [0, 1].
                                     A higher value requires closer matches. Default is 0.5.

    Returns:
        bool: True if the message matches at least one pattern above the threshold,
              False otherwise.
    """
    read_patterns = [patterns]

    # Preprocess patterns
    prepro_patterns = [preprocess_text(pattern) for pattern in read_patterns]
    vectorizer = TfidfVectorizer().fit(prepro_patterns)
    processed_msg = preprocess_text(msg)

    # Vectorize message and patterns
    vectors = vectorizer.transform([processed_msg] + prepro_patterns)
    vector_msg = vectors[0]
    patt_msg = vectors[1:]

    # Cosine similarity
    similarities = cosine_similarity(vector_msg, patt_msg)
    max_sim = similarities.max()

    return max_sim >= threshold