"""Input type detection for intelligent routing."""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class InputType(Enum):
    """Input type categories for routing."""

    NUMERICAL = "numerical"
    DATE = "date"
    DOMAIN_SPECIFIC = "domain_specific"
    GENERAL_TEXT = "general_text"


@dataclass
class DetectionResult:
    """Result of input type detection."""

    type: InputType
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


def detect_numerical(text: str) -> Optional[DetectionResult]:
    """
    Detect if input is numerical (currency, percentages, measurements).

    Examples:
        - $391B, $391 billion
        - 42%, 42 percent
        - 100kg, 100 kilograms
        - 3.14, $1,234.56
    """
    patterns = [
        r"\$?\d+\.?\d*\s*(billion|million|thousand|trillion|B|M|K|T)",
        r"\d+\.?\d*\s*%",
        r"\$\d+[,\d]*",
        r"\d+\.?\d*\s*(kg|km|lb|ft|m|cm|g|oz)",
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return DetectionResult(type=InputType.NUMERICAL, confidence=0.95)

    return None


def detect_date(text: str) -> Optional[DetectionResult]:
    """
    Detect if input is a date/time.

    Examples:
        - 10/15/2025
        - 2025-10-15
        - January 15, 2025
        - Q4 2024
    """
    patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY
        r"\d{4}-\d{2}-\d{2}",  # ISO format
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}",
        r"Q[1-4] \d{4}",  # Quarter format
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return DetectionResult(type=InputType.DATE, confidence=0.9)

    return None


def detect_domain_specific(
    text: str, domain: Optional[str] = None
) -> Optional[DetectionResult]:
    """
    Detect if input is domain-specific based on user hints.

    Requires user to provide domain metadata for accurate detection.

    Args:
        text: Input text
        domain: Domain hint (e.g., 'medical', 'legal', 'financial')
    """
    if not domain:
        return None

    # User explicitly tagged this with a domain
    return DetectionResult(
        type=InputType.DOMAIN_SPECIFIC, confidence=1.0, metadata={"domain": domain}
    )


def detect_input_type(
    expected: str, actual: str, domain: Optional[str] = None
) -> DetectionResult:
    """
    Master detector that runs all detection strategies.

    Tries detection in priority order:
    1. Domain-specific (if domain provided)
    2. Numerical
    3. Date
    4. General text (fallback)

    Args:
        expected: Expected value
        actual: Actual value
        domain: Optional domain hint

    Returns:
        DetectionResult with type and confidence
    """
    # Combine both strings for detection
    combined = f"{expected} {actual}"

    # Try detectors in priority order
    detectors = [
        lambda: detect_domain_specific(combined, domain),
        lambda: detect_numerical(expected) or detect_numerical(actual),
        lambda: detect_date(expected) or detect_date(actual),
    ]

    for detector in detectors:
        result = detector()
        if result:
            return result

    # Default: general text
    return DetectionResult(type=InputType.GENERAL_TEXT, confidence=0.7)
