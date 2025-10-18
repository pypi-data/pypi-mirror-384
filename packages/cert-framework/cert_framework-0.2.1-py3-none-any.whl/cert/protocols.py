"""Protocols for pluggable components."""

from typing import Protocol
from cert.types import ComparisonResult


class ComparatorProtocol(Protocol):
    """
    Protocol for semantic comparators.

    Any comparator must implement compare() method.
    """

    def compare(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare expected vs actual output.

        Args:
            expected: Expected output (ground truth)
            actual: Actual output from agent

        Returns:
            ComparisonResult with matched status and confidence
        """
        ...
