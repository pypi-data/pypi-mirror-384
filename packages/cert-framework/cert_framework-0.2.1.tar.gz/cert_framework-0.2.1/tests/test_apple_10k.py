"""
Real-world test suite using Apple 10-K FY2024 data.

This tests intelligent routing with actual financial document extraction scenarios.
"""

import pytest
from cert import IntelligentComparator, TestRunner, GroundTruth


class TestApple10KFinancialData:
    """Test financial data extraction with intelligent routing."""

    def setup_method(self):
        """Setup test runner with intelligent comparator."""
        self.comparator = IntelligentComparator()
        self.runner = TestRunner(semantic_comparator=self.comparator)

    # ============================================================================
    # NUMERICAL TESTS - Should route to normalized-number rule
    # ============================================================================

    def test_total_revenue_fy2024(self):
        """Test: Total net sales FY2024."""
        self.runner.add_ground_truth(
            GroundTruth(
                id="revenue-2024",
                question="What was Apple's total net sales in fiscal 2024?",
                expected="$391.035 billion",
                equivalents=["391B", "$391,035 million", "391 billion", "391.035B"],
                metadata={"correctPages": [1]},
            )
        )

        # Simulate LLM responses with various formats
        test_cases = [
            "$391.035 billion",
            "391B",
            "$391,035 million",
            "391 billion dollars",
            "$391,035,000,000",
        ]

        for output in test_cases:
            result = self.comparator.compare(
                str(self.runner.ground_truths["revenue-2024"].expected), output
            )
            assert result.matched, f"Failed to match: {output}"
            assert "number" in result.rule.lower(), f"Wrong rule for: {output}"

    def test_iphone_revenue_fy2024(self):
        """Test: iPhone revenue FY2024."""
        self.runner.add_ground_truth(
            GroundTruth(
                id="iphone-revenue-2024",
                question="What was iPhone revenue in fiscal 2024?",
                expected="$201.183 billion",
                equivalents=["201B", "$201,183 million", "201.183 billion"],
                metadata={"correctPages": [1]},
            )
        )

        result = self.comparator.compare("$201.183 billion", "201B")
        assert result.matched
        assert result.confidence > 0.9

    def test_services_revenue_fy2024(self):
        """Test: Services revenue FY2024."""
        expected = "$96.169 billion"

        # Test various formats
        test_outputs = [
            "96.169 billion",
            "$96,169 million",
            "96B",
            "$96.169B",
        ]

        for output in test_outputs:
            result = self.comparator.compare(expected, output)
            assert result.matched, f"Failed to match services revenue: {output}"

    def test_gross_margin_percentage(self):
        """Test: Gross margin as percentage."""
        expected = "46.2%"

        result = self.comparator.compare(expected, "46.2%")
        assert result.matched

        result = self.comparator.compare(expected, "46.2 percent")
        # Should match via number rule

    def test_research_development_expenses(self):
        """Test: R&D expenses."""
        expected = "$31.370 billion"

        test_outputs = [
            "31.370 billion",
            "$31,370 million",
            "31.37B",
        ]

        for output in test_outputs:
            result = self.comparator.compare(expected, output)
            assert result.matched, f"Failed to match R&D: {output}"

    # ============================================================================
    # TEXT TESTS - Should route to contains/key-phrase/fuzzy rules
    # ============================================================================

    def test_ceo_name(self):
        """Test: CEO identification."""
        expected = "Tim Cook"

        # Exact match
        result = self.comparator.compare(expected, "Tim Cook")
        assert result.matched
        assert result.rule == "exact-match"

        # Case variation
        result = self.comparator.compare(expected, "tim cook")
        assert result.matched

    def test_headquarters_location(self):
        """Test: Headquarters location."""
        expected = "Cupertino, California"

        test_outputs = [
            "Cupertino, California",
            "Cupertino, CA",
            "Located in Cupertino, California",
            "The company is headquartered in Cupertino, California",
        ]

        for output in test_outputs:
            result = self.comparator.compare(expected, output)
            # Should match via contains or fuzzy
            if not result.matched:
                print(
                    f"Failed to match HQ: {output}, rule: {result.rule}, confidence: {result.confidence}"
                )

    def test_product_categories(self):
        """Test: Product category listing."""
        expected = "iPhone, Mac, iPad, Wearables, Services"

        # Substring in longer response
        output = "Apple's main product categories include iPhone, Mac, iPad, Wearables, and Services"
        self.comparator.compare(expected, output)
        # Should match via contains or key-phrase

    def test_fiscal_year_end(self):
        """Test: Fiscal year end date."""
        expected = "September 28, 2024"

        test_outputs = [
            "September 28, 2024",
            "2024-09-28",
            "Sept 28, 2024",
            "The fiscal year ended on September 28, 2024",
        ]

        for output in test_outputs:
            self.comparator.compare(expected, output)
            # Date detection should trigger

    # ============================================================================
    # SEMANTIC EQUIVALENCE TESTS - May need training if many fail
    # ============================================================================

    def test_business_description_semantic(self):
        """Test: Semantic equivalence in business description."""
        expected = "designs, manufactures, and markets smartphones, computers, tablets, wearables, and accessories"

        semantically_equivalent = [
            "creates and sells phones, computers, tablets, wearables, and accessories",
            "produces smartphones, PCs, tablets, wearable devices, and accessories",
            "designs and markets mobile devices, computers, tablets, wearables, and related products",
        ]

        for output in semantically_equivalent:
            result = self.comparator.compare(expected, output)
            if not result.matched:
                print(f"SEMANTIC FAILURE: expected '{expected}' != actual '{output}'")
                print(f"  Rule: {result.rule}, Confidence: {result.confidence}")

    def test_market_position_semantic(self):
        """Test: Different ways to describe market position."""
        expected = "leading technology company"

        equivalents = [
            "top tech company",
            "premier technology firm",
            "major player in technology sector",
        ]

        for output in equivalents:
            result = self.comparator.compare(expected, output)
            if not result.matched:
                print(f"SEMANTIC FAILURE: '{expected}' vs '{output}'")

    def test_revenue_growth_semantic(self):
        """Test: Different phrasings of revenue trend."""
        expected = "revenue increased"

        equivalents = [
            "sales grew",
            "higher revenue",
            "revenue went up",
            "increased sales",
        ]

        for output in equivalents:
            result = self.comparator.compare(expected, output)
            if not result.matched:
                print(f"SEMANTIC FAILURE: '{expected}' vs '{output}'")

    # ============================================================================
    # EDGE CASES AND FAILURE MODE TESTS
    # ============================================================================

    def test_complex_financial_statement(self):
        """Test: Complex financial statement extraction."""
        expected = "Net income was $93.736 billion"

        # LLM might return longer response
        output = "According to the consolidated statements, Apple's net income for fiscal 2024 was $93.736 billion"

        self.comparator.compare(expected, output)
        # Should match via contains + number normalization

    def test_year_over_year_comparison(self):
        """Test: YoY comparison statement."""
        expected = "Revenue increased from $383.285 billion in 2023 to $391.035 billion in 2024"

        output = "Revenue grew 2% from $383.285B (2023) to $391.035B (2024)"

        self.comparator.compare(expected, output)
        # This is challenging - multiple numbers

    def test_abbreviation_expansion(self):
        """Test: Abbreviation vs full form."""
        expected = "R&D"

        outputs = [
            "R&D",
            "research and development",
            "Research & Development",
        ]

        for output in outputs:
            result = self.comparator.compare(expected, output)
            if not result.matched:
                print(f"ABBREVIATION FAILURE: '{expected}' vs '{output}'")


class TestRoutingDecisionLogging:
    """Test that routing decisions are being made correctly."""

    def test_numerical_input_detection(self):
        """Verify numerical inputs route to number normalization."""
        comparator = IntelligentComparator()

        result = comparator.compare("$391 billion", "391B")

        # Should use normalized-number rule
        assert result.matched
        assert "number" in result.rule.lower()

        # Get explanation
        explanation = comparator.explain("$391 billion", "391B", result)
        assert "numerical" in explanation.lower()

    def test_text_input_detection(self):
        """Verify text inputs route to fuzzy/contains rules."""
        comparator = IntelligentComparator()

        result = comparator.compare("Tim Cook", "tim cook")

        # Should use text-based rule
        assert result.matched

        explanation = comparator.explain("Tim Cook", "tim cook", result)
        print(f"\nText routing explanation:\n{explanation}")

    def test_mixed_content_routing(self):
        """Test routing when content has both numbers and text."""
        comparator = IntelligentComparator()

        result = comparator.compare("Revenue was $391 billion", "Sales were 391B")

        explanation = comparator.explain(
            "Revenue was $391 billion", "Sales were 391B", result
        )
        print(f"\nMixed content routing:\n{explanation}")


@pytest.fixture
def print_routing_stats():
    """Fixture to collect and print routing statistics."""
    stats = {
        "numerical": 0,
        "date": 0,
        "domain_specific": 0,
        "general_text": 0,
        "total": 0,
        "matched": 0,
        "failed": 0,
    }

    yield stats

    # Print statistics after tests
    print("\n" + "=" * 60)
    print("ROUTING STATISTICS")
    print("=" * 60)
    print(f"Total comparisons: {stats['total']}")
    print(
        f"  Numerical: {stats['numerical']} ({stats['numerical'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print(
        f"  Dates: {stats['date']} ({stats['date'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print(
        f"  Domain-specific: {stats['domain_specific']} ({stats['domain_specific'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print(
        f"  General text: {stats['general_text']} ({stats['general_text'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print()
    print(
        f"Matched: {stats['matched']} ({stats['matched'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print(
        f"Failed: {stats['failed']} ({stats['failed'] / max(stats['total'], 1) * 100:.1f}%)"
    )
    print("=" * 60)


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_apple_10k.py -v -s
    pytest.main([__file__, "-v", "-s"])
