"""Test runner for CERT framework."""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from .types import (
    GroundTruth,
    TestResult,
    TestConfig,
    TestStatus,
    Evidence,
)
from .consistency import measure_consistency, autodiagnose_variance
from .semantic import SemanticComparator


class ConsistencyError(Exception):
    """Raised when a consistency check fails."""

    def __init__(self, diagnosis: str, suggestions: List[str]):
        super().__init__(f"Consistency check failed: {diagnosis}")
        self.diagnosis = diagnosis
        self.suggestions = suggestions


class AccuracyError(Exception):
    """Raised when an accuracy check fails."""

    def __init__(self, diagnosis: str, expected: str, actual: str):
        super().__init__(f"Accuracy check failed: {diagnosis}")
        self.diagnosis = diagnosis
        self.expected = expected
        self.actual = actual


class TestRunner:
    """
    Test runner with pluggable semantic comparison.

    Enforces testing order: retrieval → accuracy → consistency

    Args:
        semantic_comparator: Optional custom comparator. Defaults to SemanticComparator
                           with rule-based matching. Can be replaced with EmbeddingComparator
                           or LLMJudgeComparator for different tradeoffs.

    Example:
        # Default rule-based comparison
        runner = TestRunner()

        # Embedding-based comparison (slower, better semantic matching)
        from cert.embeddings import EmbeddingComparator
        runner = TestRunner(semantic_comparator=EmbeddingComparator())

        # LLM-as-judge (slowest, most robust)
        from cert.llm_judge import LLMJudgeComparator
        runner = TestRunner(semantic_comparator=LLMJudgeComparator(client=client))
    """

    def __init__(self, semantic_comparator: Optional[Any] = None):
        """Initialize test runner with optional custom comparator."""
        self.ground_truths: Dict[str, GroundTruth] = {}
        self.results: List[TestResult] = []
        self.passed_accuracy: set[str] = set()
        self.comparator = semantic_comparator or SemanticComparator()

    def add_ground_truth(self, ground_truth: GroundTruth) -> None:
        """Register ground truth for a test."""
        self.ground_truths[ground_truth.id] = ground_truth

    def _must_have_passed_accuracy(self, test_id: str) -> None:
        """Enforce that accuracy test passed before consistency testing."""
        if test_id not in self.passed_accuracy:
            raise ValueError(
                f"Cannot test consistency for '{test_id}' before accuracy validation. "
                "Run test_accuracy() first to ensure outputs are correct."
            )

    async def test_accuracy(
        self,
        test_id: str,
        agent_fn: Callable[[], Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> TestResult:
        """
        Test accuracy against ground truth.

        Args:
            test_id: ID of test (must match ground truth ID)
            agent_fn: Async function that produces output
            config: Optional configuration

        Returns:
            TestResult with accuracy metrics
        """
        if test_id not in self.ground_truths:
            raise ValueError(f"No ground truth found for test ID: {test_id}")

        ground_truth = self.ground_truths[test_id]
        threshold = config.get("threshold", 0.8) if config else 0.8

        # Execute agent
        actual = await (
            agent_fn()
            if asyncio.iscoroutinefunction(agent_fn)
            else asyncio.to_thread(agent_fn)
        )

        # Compare with ground truth
        comparison = self.comparator.compare(str(ground_truth.expected), str(actual))

        # Check equivalents if no match
        if not comparison.matched and ground_truth.equivalents:
            for equivalent in ground_truth.equivalents:
                comparison = self.comparator.compare(equivalent, str(actual))
                if comparison.matched:
                    break

        # Determine result
        passed = comparison.matched and comparison.confidence >= threshold
        status = TestStatus.PASS if passed else TestStatus.FAIL

        result = TestResult(
            test_id=test_id,
            status=status,
            timestamp=datetime.now(),
            accuracy=comparison.confidence if comparison.matched else 0.0,
            diagnosis=None
            if passed
            else (
                f"Output '{actual}' does not match expected '{ground_truth.expected}'"
            ),
            suggestions=None
            if passed
            else [
                "Check if the agent is retrieving correct context",
                "Verify prompt clearly specifies expected output format",
                "Consider adding equivalents to ground truth",
            ],
        )

        if passed:
            self.passed_accuracy.add(test_id)

        self.results.append(result)
        return result

    async def test_consistency(
        self, test_id: str, agent_fn: Callable[[], Any], config: TestConfig
    ) -> TestResult:
        """
        Test consistency across multiple runs.

        Args:
            test_id: ID of test
            agent_fn: Async function to test
            config: Test configuration

        Returns:
            TestResult with consistency metrics
        """
        # Layer enforcement
        self._must_have_passed_accuracy(test_id)

        # Measure consistency
        consistency_result = await measure_consistency(agent_fn, config)

        # Determine pass/fail
        passed = consistency_result.consistency >= config.consistency_threshold
        status = TestStatus.PASS if passed else TestStatus.FAIL

        # Build result
        result = TestResult(
            test_id=test_id,
            status=status,
            timestamp=datetime.now(),
            consistency=consistency_result.consistency,
            evidence=Evidence(
                outputs=[str(o) for o in consistency_result.outputs],
                unique_count=consistency_result.unique_count,
                examples=consistency_result.evidence,
            )
            if not passed
            else None,
            diagnosis=autodiagnose_variance(consistency_result) if not passed else None,
            suggestions=[
                "Set temperature=0 if not already",
                "Check for non-deterministic data sources (timestamps, random sampling)",
                "Review prompt for ambiguous instructions",
                "Consider using semantic comparison if outputs are semantically equivalent",
            ]
            if not passed
            else None,
        )

        self.results.append(result)
        return result

    def get_results(self, test_id: Optional[str] = None) -> List[TestResult]:
        """
        Get test results.

        Args:
            test_id: Optional filter by test ID

        Returns:
            List of test results
        """
        if test_id:
            return [r for r in self.results if r.test_id == test_id]
        return self.results
