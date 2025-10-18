"""Type definitions for CERT framework."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class TestStatus(str, Enum):
    """Status of a test result."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class GroundTruth:
    """Definition of expected output for accuracy testing."""

    id: str
    question: str
    expected: Union[str, int, float, Dict[str, Any]]
    equivalents: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestConfig:
    """Configuration for running tests."""

    n_trials: int = 10
    consistency_threshold: float = 0.9
    accuracy_threshold: float = 0.8
    semantic_comparison: bool = True
    timeout: int = 30000  # milliseconds


@dataclass
class Evidence:
    """Evidence of test variance."""

    outputs: List[str]
    unique_count: int
    examples: List[str]


@dataclass
class TestResult:
    """Result of a test execution."""

    test_id: str
    status: TestStatus
    timestamp: datetime = field(default_factory=datetime.now)
    consistency: Optional[float] = None
    accuracy: Optional[float] = None
    evidence: Optional[Evidence] = None
    diagnosis: Optional[str] = None
    suggestions: Optional[List[str]] = None
    human_annotation: Optional["HumanAnnotation"] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "testId": self.test_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "consistency": self.consistency,
            "accuracy": self.accuracy,
            "evidence": {
                "outputs": self.evidence.outputs,
                "uniqueCount": self.evidence.unique_count,
                "examples": self.evidence.examples,
            }
            if self.evidence
            else None,
            "diagnosis": self.diagnosis,
            "suggestions": self.suggestions,
            "humanAnnotation": self.human_annotation.to_dict()
            if self.human_annotation
            else None,
        }


@dataclass
class ConsistencyResult:
    """Result of consistency measurement."""

    consistency: float
    outputs: List[Any]
    unique_count: int
    evidence: List[str]


@dataclass
class DegradationAlert:
    """Alert for test performance degradation."""

    test_id: str
    message: str
    severity: str  # 'info', 'warning', 'critical'


@dataclass
class HumanAnnotation:
    """Human annotation of test result equivalence."""

    id: str
    test_id: str
    expected: str
    actual: str
    equivalent: bool
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "testId": self.test_id,
            "expected": self.expected,
            "actual": self.actual,
            "equivalent": self.equivalent,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "domain": self.domain,
        }


@dataclass
class ComparisonResult:
    """Result of semantic comparison.

    Can be used as a boolean for simple checks:
        if compare(text1, text2):
            print("Match!")

    Or access detailed information:
        result = compare(text1, text2)
        print(f"Confidence: {result.confidence:.1%}")
    """

    matched: bool
    rule: Optional[str] = None
    confidence: float = 0.0

    def __bool__(self) -> bool:
        """Allow using result as boolean: if compare(text1, text2): ..."""
        return self.matched

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "Match" if self.matched else "No match"
        return f"{status} (confidence: {self.confidence:.1%})"
