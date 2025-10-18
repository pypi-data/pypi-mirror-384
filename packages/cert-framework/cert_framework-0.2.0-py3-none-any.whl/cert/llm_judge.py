"""LLM-as-judge semantic comparison."""

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from cert.types import ComparisonResult


class LLMJudgeComparator:
    """
    Semantic comparator using LLM-as-judge.

    Most robust for:
    - Complex semantic equivalence
    - Domain-specific terminology
    - High-stakes decisions

    Tradeoffs:
    - Slowest: ~500-1000ms per comparison
    - Requires API key and internet connection
    - Non-deterministic (can vary across calls)
    - Cost: ~$0.00005 per comparison (Claude Haiku)

    Args:
        client: Anthropic client instance
        model: Model to use for judging (default: claude-haiku)
        temperature: Temperature for judge (0 = deterministic)

    Example:
        import anthropic
        client = anthropic.Anthropic(api_key="...")

        comparator = LLMJudgeComparator(client)
        result = comparator.compare(
            "STEMI",
            "ST-elevation myocardial infarction - activate cath lab"
        )
        # result.matched = True, confidence = 0.95
    """

    def __init__(
        self,
        client: "anthropic.Anthropic",
        model: str = "claude-haiku-4-20250514",
        temperature: float = 0,
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic not installed. Install with:\n"
                "  pip install cert-framework[llm-judge]"
            )

        self.client = client
        self.model = model
        self.temperature = temperature

    def compare(self, expected: str, actual: str) -> ComparisonResult:
        """
        Use LLM to judge if actual matches expected semantically.

        Returns:
            ComparisonResult based on LLM's judgment
        """
        prompt = f"""You are evaluating if two outputs are semantically equivalent.

Expected output: "{expected}"
Actual output: "{actual}"

Are these semantically equivalent? Consider:
- Do they convey the same core meaning?
- Would they be considered correct answers to the same question?
- Ignore differences in phrasing, verbosity, or formatting

Respond in JSON format:
{{
  "equivalent": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

IMPORTANT: Respond ONLY with valid JSON, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            import json

            result_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)

            return ComparisonResult(
                matched=result["equivalent"],
                rule="llm-judge",
                confidence=result["confidence"],
            )

        except Exception:
            # On error, fall back to conservative judgment
            return ComparisonResult(
                matched=False, rule="llm-judge-error", confidence=0.0
            )
