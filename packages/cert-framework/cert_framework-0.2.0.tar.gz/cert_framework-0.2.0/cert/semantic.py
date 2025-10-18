"""Semantic comparison engine with pluggable rules."""

import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Union


@dataclass
class ComparisonResult:
    """Result of a semantic comparison."""

    matched: bool
    rule: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ComparisonRule:
    """A pluggable comparison rule."""

    name: str
    priority: int
    match: Callable[[str, str], Union[bool, float]]


class SemanticComparator:
    """
    Semantic comparator with pluggable rules.

    Rules are checked in priority order (highest first).
    """

    def __init__(self):
        """Initialize with default rules."""
        self.rules: List[ComparisonRule] = []
        self._add_default_rules()

    def _add_default_rules(self) -> None:
        """Add built-in comparison rules."""
        self.add_rule(exact_match_rule())
        self.add_rule(normalized_number_rule())
        self.add_rule(contains_match_rule())
        self.add_rule(key_phrase_rule())
        self.add_rule(fuzzy_text_rule())

    def add_rule(self, rule: ComparisonRule) -> None:
        """Add a comparison rule."""
        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def compare(self, expected: str, actual: str) -> ComparisonResult:
        """
        Compare two strings using registered rules.

        Args:
            expected: Expected value
            actual: Actual value

        Returns:
            ComparisonResult indicating match status
        """
        for rule in self.rules:
            result = rule.match(expected, actual)
            # Now all rules return float (0.0-1.0)
            if result > 0.0:
                return ComparisonResult(matched=True, rule=rule.name, confidence=result)

        return ComparisonResult(matched=False, confidence=0.0)


def exact_match_rule() -> ComparisonRule:
    """Rule for exact string matching."""

    def match(expected: str, actual: str) -> Union[bool, float]:
        return 1.0 if expected == actual else 0.0

    return ComparisonRule(name="exact-match", priority=100, match=match)


def normalized_number_rule() -> ComparisonRule:
    """Rule for matching numbers with different formatting."""

    def extract_number(text: str) -> Optional[dict]:
        """Extract number and unit from text."""
        # Remove currency symbols and commas
        text = re.sub(r"[$,£€¥]", "", text)

        # Match number with optional unit - more aggressive pattern
        pattern = (
            r"(\d+(?:\.\d+)?)\s*(billion|million|thousand|trillion|%|percent|B|M|K|T)?"
        )

        matches = re.finditer(pattern, text, re.IGNORECASE)

        # Get all matches, return the first valid one
        for match in matches:
            try:
                value = float(match.group(1))
                unit = (match.group(2) or "").lower()
                return {"value": value, "unit": unit}
            except (ValueError, AttributeError):
                continue

        return None

    def normalize_to_base(value: float, unit: str) -> float:
        """Normalize number to base unit."""
        multipliers = {
            "trillion": 1e12,
            "t": 1e12,
            "billion": 1e9,
            "b": 1e9,
            "million": 1e6,
            "m": 1e6,
            "thousand": 1e3,
            "k": 1e3,
            "%": 0.01,
            "percent": 0.01,
            "": 1,
        }
        return value * multipliers.get(unit, 1)

    def match(expected: str, actual: str) -> Union[bool, float]:
        # Fast rejection: if neither string contains digits, this isn't a number comparison
        if not any(c.isdigit() for c in expected) or not any(
            c.isdigit() for c in actual
        ):
            return 0.0

        exp_num = extract_number(expected)
        act_num = extract_number(actual)

        if not exp_num or not act_num:
            return 0.0

        exp_val = normalize_to_base(exp_num["value"], exp_num["unit"])
        act_val = normalize_to_base(act_num["value"], act_num["unit"])

        # Allow 0.1% difference
        if exp_val == 0:
            return 1.0 if act_val == 0 else 0.0

        diff = abs(exp_val - act_val) / exp_val
        return 1.0 if diff < 0.001 else 0.0

    return ComparisonRule(name="normalized-number", priority=95, match=match)


def contains_match_rule() -> ComparisonRule:
    """Match if expected appears as substring in actual after normalization."""

    def normalize(text: str) -> str:
        """Normalize for comparison."""
        return " ".join(text.lower().split())

    def match(expected: str, actual: str) -> Union[bool, float]:
        exp_norm = normalize(expected)
        act_norm = normalize(actual)

        # If expected is in actual
        if exp_norm in act_norm:
            return 0.95  # High confidence substring match

        # If actual is in expected (reversed)
        if act_norm in exp_norm:
            return 0.95

        return 0.0

    return ComparisonRule(
        name="contains-match",
        priority=90,  # Between exact (100) and number (95)
        match=match,
    )


def key_phrase_rule() -> ComparisonRule:
    """Match based on word overlap between short phrases."""

    def get_content_words(text: str) -> set:
        """Extract meaningful words, excluding stopwords."""
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "of",
            "in",
            "to",
            "for",
            "and",
            "or",
            "but",
        }
        words = text.lower().split()
        return {w for w in words if w not in stopwords and len(w) > 2}

    def match(expected: str, actual: str) -> Union[bool, float]:
        exp_words = get_content_words(expected)
        act_words = get_content_words(actual)

        if not exp_words:
            return 0.0

        # Jaccard similarity
        intersection = exp_words & act_words
        union = exp_words | act_words

        if not union:
            return 0.0

        similarity = len(intersection) / len(union)

        # Return confidence if similarity is high enough
        return similarity if similarity > 0.5 else 0.0

    return ComparisonRule(
        name="key-phrase",
        priority=85,  # After contains, before fuzzy
        match=match,
    )


def fuzzy_text_rule() -> ComparisonRule:
    """Rule for fuzzy text matching."""

    def normalize(text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r"[^\w\s]", "", text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def match(expected: str, actual: str) -> Union[bool, float]:
        norm_exp = normalize(expected)
        norm_act = normalize(actual)

        if norm_exp == norm_act:
            return 1.0

        # Check if one contains the other
        if norm_exp in norm_act or norm_act in norm_exp:
            return 0.9

        # Try fuzzy matching if rapidfuzz is available
        try:
            from rapidfuzz import fuzz

            ratio = fuzz.ratio(norm_exp, norm_act) / 100.0
            return ratio if ratio > 0.85 else 0.0
        except ImportError:
            return 0.0

    return ComparisonRule(name="fuzzy-text", priority=70, match=match)
