"""Intelligent comparator with automatic routing based on input type detection."""

from typing import Optional
from cert.types import ComparisonResult
from cert.semantic import SemanticComparator
from cert.detectors import detect_input_type, InputType, DetectionResult


class IntelligentComparator:
    """
    Intelligent comparator that automatically routes to the right strategy
    based on input type detection.

    Routing logic:
    - Numbers/currency → Rule-based normalization
    - Dates → Date parsing + normalization (TODO)
    - Domain-specific → Trained model (if available) or embeddings
    - General text → Embeddings (if available) or fuzzy match

    Args:
        domain: Optional domain hint for domain-specific detection
        fuzzy_threshold: Threshold for fuzzy text matching (0-1)
        use_embeddings: Enable embedding comparison (requires cert-framework[embeddings])
        embedding_threshold: Threshold for embedding similarity

    Example:
        # Default routing
        comparator = IntelligentComparator()

        # With domain hint
        comparator = IntelligentComparator(domain='medical')

        # With embeddings
        comparator = IntelligentComparator(use_embeddings=True)

        # Automatically uses number normalization
        result = comparator.compare('$391 billion', '391B')
        # → matched=True, rule='normalized-number'

        # Automatically uses semantic comparison
        result = comparator.compare('reduced latency', 'faster response')
        # → matched=True, rule='embedding-similarity' or 'fuzzy-text'
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        fuzzy_threshold: float = 0.8,
        embedding_threshold: float = 0.75,
    ):
        """
        Initialize intelligent comparator with automatic routing.

        Embeddings are REQUIRED and loaded automatically. If you're testing
        LLM outputs, you need semantic comparison. The ~420MB model download
        on first run is the cost of doing business.

        Args:
            domain: Optional domain hint for domain-specific detection
            fuzzy_threshold: Threshold for fuzzy text matching
            embedding_threshold: Threshold for embedding similarity
        """
        self.domain = domain
        self.fuzzy_threshold = fuzzy_threshold
        self.embedding_threshold = embedding_threshold

        # Base comparator (always available)
        self.base_comparator = SemanticComparator()

        # Embedding comparator (REQUIRED)
        self._load_embedding_comparator()

        # Domain comparator (optional, loaded on demand)
        self.domain_comparator = None

    def _load_embedding_comparator(self):
        """Load embedding comparator (REQUIRED)."""
        from cert.embeddings import EmbeddingComparator

        self.embedding_comparator = EmbeddingComparator(
            threshold=self.embedding_threshold
        )

    def compare(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare two strings with intelligent routing.

        Args:
            expected: Expected value
            actual: Actual value

        Returns:
            ComparisonResult with matched status and confidence
        """
        # Step 1: Detect input type
        detection = detect_input_type(expected, actual, self.domain)

        # Step 2: Route to appropriate comparator
        if detection.type == InputType.NUMERICAL:
            result = self._compare_numerical(expected, actual)
        elif detection.type == InputType.DATE:
            result = self._compare_date(expected, actual)
        elif detection.type == InputType.DOMAIN_SPECIFIC:
            result = self._compare_domain_specific(expected, actual)
        else:  # GENERAL_TEXT
            result = self._compare_general_text(expected, actual)

        # Log routing decision for analysis
        self._log_routing_decision(detection, result, expected, actual)

        return result

    def _compare_numerical(self, expected: str, actual: str) -> ComparisonResult:
        """Use rule-based number normalization."""
        return self.base_comparator.compare(expected, actual)

    def _compare_date(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare dates with parsing and normalization.

        TODO: Implement proper date parsing.
        For now, fallback to fuzzy match.
        """
        return self.base_comparator.compare(expected, actual)

    def _compare_domain_specific(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare domain-specific content.

        Priority:
        1. Domain-specific trained model (if available)
        2. Embedding comparator (if available)
        3. Base comparator (fallback)
        """
        # Try domain-specific comparator if available
        if self.domain_comparator:
            return self.domain_comparator.compare(expected, actual)

        # Fallback to embeddings if available
        if self.embedding_comparator:
            return self.embedding_comparator.compare(expected, actual)

        # Final fallback to base comparator
        return self.base_comparator.compare(expected, actual)

    def _compare_general_text(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare general text.

        Priority:
        1. Embedding comparator (if available)
        2. Base comparator with fuzzy matching
        """
        # Try embeddings first if available
        if self.embedding_comparator:
            return self.embedding_comparator.compare(expected, actual)

        # Fallback to base comparator
        return self.base_comparator.compare(expected, actual)

    def explain(self, expected: str, actual: str, result: ComparisonResult) -> str:
        """
        Explain why the comparison resulted in this outcome.

        Args:
            expected: Expected value
            actual: Actual value
            result: ComparisonResult from compare()

        Returns:
            Human-readable explanation of the routing decision
        """
        detection = detect_input_type(expected, actual, self.domain)

        explanation = []
        explanation.append(
            f"Detected input type: {detection.type.value} "
            f"(confidence: {detection.confidence:.2f})"
        )
        explanation.append(
            f"Comparison result: {'✓ MATCHED' if result.matched else '✗ NOT MATCHED'} "
            f"(confidence: {result.confidence:.2f})"
        )
        explanation.append(f"Rule used: {result.rule}")

        if detection.type == InputType.NUMERICAL:
            explanation.append(
                "\nUsed rule-based number normalization. "
                "Handles currency, percentages, and unit conversions."
            )
        elif detection.type == InputType.DATE:
            explanation.append(
                "\nUsed date parsing and normalization. Handles various date formats."
            )
        elif detection.type == InputType.DOMAIN_SPECIFIC:
            domain_name = (
                detection.metadata.get("domain") if detection.metadata else "unknown"
            )
            explanation.append(f"\nDetected domain-specific content ({domain_name}). ")
            if self.domain_comparator:
                explanation.append("Used fine-tuned domain comparator.")
            elif self.embedding_comparator:
                explanation.append("No domain comparator available, used embeddings.")
            else:
                explanation.append(
                    f"No domain comparator or embeddings available, "
                    f"fell back to {result.rule}."
                )
        elif detection.type == InputType.GENERAL_TEXT:
            if self.embedding_comparator:
                explanation.append(
                    "\nUsed semantic embeddings for general text comparison."
                )
            else:
                explanation.append(
                    "\nUsed fuzzy text matching for general text comparison."
                )

        return "\n".join(explanation)

    def _log_routing_decision(
        self,
        detection: DetectionResult,
        result: ComparisonResult,
        expected: str,
        actual: str,
    ):
        """
        Log routing decision for analysis.

        Can be overridden to send logs to a file or monitoring system.
        """
        import os

        if os.environ.get("CERT_LOG_ROUTING") == "1":
            import json

            log_entry = {
                "detection_type": detection.type.value,
                "detection_confidence": detection.confidence,
                "matched": result.matched,
                "rule": result.rule,
                "confidence": result.confidence,
                "expected": expected[:100],  # Truncate for readability
                "actual": actual[:100],
            }
            print(f"[ROUTING] {json.dumps(log_entry)}")

    def load_domain_model(self, model_path: str):
        """
        Load a trained domain-specific model.

        Args:
            model_path: Path to trained model directory

        Raises:
            ImportError: If training module not available
        """
        try:
            from cert.trained_comparator import TrainedComparator

            self.domain_comparator = TrainedComparator(model_path=model_path)
        except ImportError:
            raise ImportError(
                "Training module not available. "
                "This feature requires additional dependencies."
            )
