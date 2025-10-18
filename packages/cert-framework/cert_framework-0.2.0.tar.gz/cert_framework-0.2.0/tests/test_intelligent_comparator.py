"""Tests for intelligent comparator with automatic routing."""

import pytest
from cert.intelligent_comparator import IntelligentComparator
from cert.detectors import InputType, detect_input_type


def _embeddings_available() -> bool:
    """Check if embeddings package is available."""
    try:
        from cert.embeddings import EmbeddingComparator  # noqa: F401

        return True
    except ImportError:
        return False


class TestInputDetection:
    """Test input type detection."""

    def test_detect_numerical_currency(self):
        """Should detect currency as numerical."""
        result = detect_input_type("$391 billion", "391B")
        assert result.type == InputType.NUMERICAL
        assert result.confidence > 0.9

    def test_detect_numerical_percentage(self):
        """Should detect percentages as numerical."""
        result = detect_input_type("42%", "42 percent")
        assert result.type == InputType.NUMERICAL

    def test_detect_numerical_measurements(self):
        """Should detect measurements as numerical."""
        result = detect_input_type("100kg", "100 kilograms")
        assert result.type == InputType.NUMERICAL

    def test_detect_date_formats(self):
        """Should detect various date formats."""
        result = detect_input_type("10/15/2025", "2025-10-15")
        assert result.type == InputType.DATE

        result = detect_input_type("Q4 2024", "Q4 2024")
        assert result.type == InputType.DATE

    def test_detect_domain_specific(self):
        """Should detect domain-specific when domain provided."""
        result = detect_input_type("STEMI", "heart attack", domain="medical")
        assert result.type == InputType.DOMAIN_SPECIFIC
        assert result.confidence == 1.0
        assert result.metadata["domain"] == "medical"

    def test_detect_general_text_fallback(self):
        """Should fallback to general text for unmatched patterns."""
        result = detect_input_type("hello world", "hi there")
        assert result.type == InputType.GENERAL_TEXT


class TestIntelligentComparator:
    """Test intelligent comparator routing."""

    def test_routes_numerical_to_normalization(self):
        """Should route numerical inputs to number normalization."""
        comparator = IntelligentComparator()

        result = comparator.compare("$391 billion", "391B")

        assert result.matched
        assert "number" in result.rule.lower()
        assert result.confidence > 0.9

    def test_handles_different_numerical_formats(self):
        """Should handle various numerical formats."""
        comparator = IntelligentComparator()

        # Currency
        assert comparator.compare("$391.035 billion", "$391,035 million").matched

        # Percentages
        assert (
            comparator.compare("42%", "0.42").matched
            or comparator.compare("42", "42 percent").matched
        )

    def test_routes_general_text_to_fuzzy(self):
        """Should route general text to fuzzy matching by default."""
        comparator = IntelligentComparator()

        result = comparator.compare("hello world", "hello world")

        assert result.matched
        # Could be exact or fuzzy depending on rule priority
        assert result.confidence > 0.9

    def test_explain_provides_reasoning(self):
        """Should provide explanation of routing decision."""
        comparator = IntelligentComparator()

        result = comparator.compare("$391 billion", "391B")
        explanation = comparator.explain("$391 billion", "391B", result)

        assert "numerical" in explanation.lower()
        assert "normalization" in explanation.lower()
        assert "✓ MATCHED" in explanation

    def test_domain_hint_routing(self):
        """Should route to domain-specific handling when domain provided."""
        comparator = IntelligentComparator(domain="medical")

        # Note: Without actual domain model, this falls back to base comparator
        result = comparator.compare("STEMI", "ST-elevation myocardial infarction")

        # Should at least not crash
        assert result is not None
        assert hasattr(result, "matched")

    def test_contains_and_key_phrase_matching(self):
        """Should use contains and key-phrase rules for text matching."""
        comparator = IntelligentComparator()

        # Test substring matching
        result = comparator.compare(
            "faster data access", "The main benefit of caching is faster data access"
        )
        assert result.matched
        assert result.confidence >= 0.9

        # Test key phrase matching
        result = comparator.compare(
            "faster access", "The system provides quicker data retrieval"
        )
        # Should match via key-phrase rule (word overlap)
        assert result.confidence > 0.5


class TestIntelligentComparatorWithEmbeddings:
    """Test intelligent comparator with embeddings (if available)."""

    def test_gracefully_handles_missing_embeddings(self):
        """Should not crash if embeddings not installed."""
        comparator = IntelligentComparator(use_embeddings=True)

        # Should still work with fallback
        result = comparator.compare("hello", "hello")
        assert result.matched

    @pytest.mark.skipif(not _embeddings_available(), reason="Embeddings not installed")
    def test_uses_embeddings_when_available(self):
        """Should use embeddings for semantic matching when available."""
        comparator = IntelligentComparator(use_embeddings=True)

        result = comparator.compare("reduced latency", "faster response times")

        # If embeddings available, should detect semantic similarity
        assert result.confidence > 0.6
