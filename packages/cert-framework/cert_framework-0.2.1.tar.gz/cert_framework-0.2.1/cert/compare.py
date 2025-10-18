"""Simple API for document comparison.

This module provides a simple, one-function interface to CERT:

    from cert import compare

    result = compare("revenue increased", "sales grew")
    if result:
        print(f"Match! Confidence: {result.confidence:.1%}")

Progressive disclosure: simple by default, configurable for advanced use.
"""

from typing import Optional
from cert.embeddings import EmbeddingComparator, ComparisonResult

# Global comparator with lazy initialization
_default_comparator: Optional[EmbeddingComparator] = None


def compare(
    text1: str, text2: str, threshold: Optional[float] = None
) -> ComparisonResult:
    """Compare two texts for semantic similarity.

    This is the simplest way to use CERT. One function call, immediate value.

    Args:
        text1: First text to compare
        text2: Second text to compare
        threshold: Optional custom threshold (0-1). If None, uses default 0.80

    Returns:
        ComparisonResult with matched (bool) and confidence (float) attributes

    Raises:
        TypeError: If text1 or text2 are not strings
        ValueError: If texts are empty or threshold is out of range

    Example:
        Basic usage:
            result = compare("revenue increased", "sales grew")
            print(result.matched)  # True
            print(result.confidence)  # 0.847

        As boolean:
            if compare("profit up", "earnings rose"):
                print("Match!")

        Custom threshold:
            result = compare("good", "great", threshold=0.90)

    Note:
        First call downloads the embedding model (~420MB). Subsequent calls
        are fast (~50-100ms per comparison).

        Uses all-mpnet-base-v2 model with 0.80 threshold (87.6% accuracy on
        STS-Benchmark). Validated on 8,628 human-annotated pairs.
    """
    # Validate inputs
    if not isinstance(text1, str) or not isinstance(text2, str):
        raise TypeError(
            f"Both texts must be strings. Got {type(text1).__name__} and {type(text2).__name__}"
        )

    if not text1.strip() or not text2.strip():
        raise ValueError(
            "Cannot compare empty texts. Both text1 and text2 must contain content."
        )

    if threshold is not None and not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    global _default_comparator

    # Lazy initialization: load model on first use
    if _default_comparator is None:
        print("Loading semantic model (one-time, ~5 seconds)...")
        _default_comparator = EmbeddingComparator()

    # Custom threshold for this comparison
    if threshold is not None:
        old_threshold = _default_comparator.threshold
        _default_comparator.threshold = threshold
        result = _default_comparator.compare(text1, text2)
        _default_comparator.threshold = old_threshold
        return result

    return _default_comparator.compare(text1, text2)


def configure(
    model_name: str = "sentence-transformers/all-mpnet-base-v2", threshold: float = 0.80
) -> None:
    """Configure the default comparison model and threshold.

    Call this once at application startup if you want to use a different
    model or threshold for all comparisons.

    Args:
        model_name: Sentence transformer model to use
        threshold: Similarity threshold (0-1)

    Example:
        # Use faster but less accurate model
        configure(model_name="all-MiniLM-L6-v2", threshold=0.75)

        # Then all compare() calls use these settings
        result = compare("text1", "text2")

    Note:
        This replaces the global comparator, so any cached embeddings are lost.
    """
    global _default_comparator
    _default_comparator = EmbeddingComparator(
        model_name=model_name, threshold=threshold
    )


def reset() -> None:
    """Reset the global comparator (mainly for testing)."""
    global _default_comparator
    _default_comparator = None
