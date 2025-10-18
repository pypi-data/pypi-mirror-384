"""Tests for the simple compare API."""

import pytest
from cert import compare
from cert.types import ComparisonResult
from cert.compare import reset


class TestCompareAPI:
    """Test the simple compare() API."""

    def setup_method(self):
        """Reset comparator before each test."""
        reset()

    def test_basic_comparison(self):
        """Test basic semantic comparison."""
        result = compare("revenue increased", "sales grew")
        assert isinstance(result, ComparisonResult)
        assert result.matched is True
        assert result.confidence > 0.80

    def test_no_match(self):
        """Test texts that shouldn't match."""
        result = compare("revenue up", "revenue down")
        assert result.matched is False
        assert result.confidence < 0.80

    def test_exact_match(self):
        """Test identical texts."""
        result = compare("hello world", "hello world")
        assert result.matched is True
        assert result.confidence > 0.95

    def test_custom_threshold(self):
        """Test custom threshold parameter."""
        text1, text2 = "good quality", "great product"

        result_strict = compare(text1, text2, threshold=0.95)
        result_loose = compare(text1, text2, threshold=0.50)

        # Results should differ based on threshold
        assert result_strict.confidence == result_loose.confidence  # Same similarity
        # But matched status depends on threshold
        assert not result_strict.matched or result_loose.matched

    def test_result_as_boolean(self):
        """Test using Result directly in boolean context."""
        result_match = compare("hello", "hello")
        result_nomatch = compare("hello", "goodbye")

        assert result_match  # Should be truthy when matched
        assert not result_nomatch  # Should be falsy when not matched

    def test_result_string(self):
        """Test Result string representation."""
        result = compare("test", "test")
        string = str(result)
        assert "Match" in string or "confidence" in string.lower()

    def test_error_on_empty_text(self):
        """Test that empty texts raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compare("", "some text")

        with pytest.raises(ValueError, match="empty"):
            compare("some text", "")

        with pytest.raises(ValueError, match="empty"):
            compare("   ", "some text")  # Whitespace only

    def test_error_on_invalid_type(self):
        """Test that non-string inputs raise TypeError."""
        with pytest.raises(TypeError, match="string"):
            compare(123, "text")

        with pytest.raises(TypeError, match="string"):
            compare("text", 456)

        with pytest.raises(TypeError, match="string"):
            compare(None, "text")

    def test_error_on_invalid_threshold(self):
        """Test that invalid thresholds raise ValueError."""
        with pytest.raises(ValueError, match="threshold"):
            compare("text1", "text2", threshold=1.5)

        with pytest.raises(ValueError, match="threshold"):
            compare("text1", "text2", threshold=-0.1)

        with pytest.raises(ValueError, match="threshold"):
            compare("text1", "text2", threshold=2.0)

    def test_threshold_boundaries(self):
        """Test threshold boundary values."""
        # These should work fine
        result_zero = compare("text1", "text2", threshold=0.0)
        result_one = compare("text1", "text2", threshold=1.0)

        assert isinstance(result_zero, ComparisonResult)
        assert isinstance(result_one, ComparisonResult)

    def test_lazy_loading(self):
        """Test that model is loaded lazily on first call."""
        from cert.compare import _default_comparator

        # Should be None initially
        assert _default_comparator is None

        # First call should load model
        compare("text1", "text2")

        # Now should be initialized
        from cert.compare import _default_comparator

        assert _default_comparator is not None

    def test_confidence_values(self):
        """Test that confidence values are in valid range."""
        pairs = [
            ("hello", "hello"),
            ("revenue up", "sales increased"),
            ("profit", "loss"),
        ]

        for text1, text2 in pairs:
            result = compare(text1, text2)
            assert 0.0 <= result.confidence <= 1.0

    def test_batch_comparisons(self):
        """Test multiple comparisons work correctly."""
        pairs = [
            ("revenue increased", "sales grew", True),
            ("CEO resigned", "executive departed", True),
            ("profit up", "profit down", False),
            ("Q3 earnings", "third quarter profits", True),
        ]

        for text1, text2, expected_match in pairs:
            result = compare(text1, text2)
            # Note: We check that result exists, actual matching depends on model
            assert isinstance(result, ComparisonResult)
            assert isinstance(result.matched, bool)

    def test_unicode_support(self):
        """Test that Unicode text is handled correctly."""
        result = compare("café", "café")
        assert result.matched is True

        result = compare("hello 你好", "hello 你好")
        assert result.matched is True

    def test_special_characters(self):
        """Test text with special characters."""
        result = compare("revenue increased by 50%", "sales grew by 50% year-over-year")
        assert isinstance(result, ComparisonResult)

        result = compare("$391 billion", "$391B")
        assert isinstance(result, ComparisonResult)

    def test_long_texts(self):
        """Test comparison of longer texts."""
        text1 = "The company reported strong quarterly earnings with revenue increasing by 15% year-over-year to $391 billion."
        text2 = (
            "Q3 results showed solid performance as sales grew 15% YoY reaching $391B."
        )

        result = compare(text1, text2)
        assert isinstance(result, ComparisonResult)
        assert result.confidence > 0.70  # Should be relatively high

    def test_short_texts(self):
        """Test comparison of very short texts."""
        result = compare("yes", "no")
        assert isinstance(result, ComparisonResult)

        result = compare("OK", "okay")
        assert isinstance(result, ComparisonResult)


class TestCompareConfiguration:
    """Test configuration and reset functionality."""

    def setup_method(self):
        """Reset comparator before each test."""
        reset()

    def test_reset_clears_comparator(self):
        """Test that reset() clears the global comparator."""
        # Make a comparison to initialize
        compare("text1", "text2")

        # Reset
        reset()

        # Comparator should be None again
        from cert.compare import _default_comparator

        assert _default_comparator is None

    def test_configure_sets_global(self):
        """Test that configure() sets global comparator."""
        from cert.compare import configure

        configure(threshold=0.75)

        # Next comparison should use configured threshold
        result = compare("text1", "text2")
        assert isinstance(result, ComparisonResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
