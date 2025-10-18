"""Quick domain-specific validation with hand-crafted examples.

Tests if embeddings handle domain-specific terminology well enough
to avoid needing fine-tuning.

Target: >85% accuracy = ship it, 70-85% = consider training
"""

from cert.embeddings import EmbeddingComparator


def test_financial_terminology():
    """Test financial domain vocabulary substitutions."""
    comparator = EmbeddingComparator(threshold=0.80)  # Using optimal threshold from STS

    test_cases = [
        # (expected, actual, should_match)
        ("revenue increased", "sales grew", True),
        ("revenue decreased", "sales grew", False),
        (
            "EBITDA",
            "earnings before interest, taxes, depreciation, and amortization",
            True,
        ),
        ("operating income", "EBIT", True),
        ("net income", "bottom line", True),
        ("cash flow", "liquidity", True),
        ("market capitalization", "market cap", True),
        ("year-over-year", "YoY", True),
        ("quarter-over-quarter", "QoQ", True),
        ("fiscal year", "FY", True),
        ("gross margin", "gross profit margin", True),
        ("total revenue", "top line", True),
        ("operating expenses", "OpEx", True),
        ("capital expenditure", "CapEx", True),
        ("return on equity", "ROE", True),
        ("accounts receivable", "AR", True),
        ("accounts payable", "AP", True),
        ("cost of goods sold", "COGS", True),
        ("price-to-earnings", "P/E ratio", True),
        ("earnings per share", "EPS", True),
        # Negative cases
        ("revenue", "expenses", False),
        ("assets", "liabilities", False),
        ("profit", "loss", False),
    ]

    print("\n=== Financial Terminology Tests ===")
    results = []
    for expected, actual, should_match in test_cases:
        result = comparator.compare(expected, actual)
        matched = result.matched
        confidence = result.confidence

        status = "✓" if matched == should_match else "✗"
        print(
            f"{status} '{expected}' vs '{actual}': {matched} (conf: {confidence:.3f}) [expected: {should_match}]"
        )

        results.append(matched == should_match)

    accuracy = sum(results) / len(results)
    print(f"\nFinancial Accuracy: {accuracy:.1%} ({sum(results)}/{len(results)})")

    return accuracy


def test_medical_terminology():
    """Test medical domain vocabulary substitutions."""
    comparator = EmbeddingComparator(threshold=0.80)

    test_cases = [
        # (expected, actual, should_match)
        ("STEMI", "ST-elevation myocardial infarction", True),
        ("MI", "myocardial infarction", True),
        ("MI", "heart attack", True),
        ("HTN", "hypertension", True),
        ("HTN", "high blood pressure", True),
        ("DM", "diabetes mellitus", True),
        ("CVA", "cerebrovascular accident", True),
        ("CVA", "stroke", True),
        ("COPD", "chronic obstructive pulmonary disease", True),
        ("CHF", "congestive heart failure", True),
        ("AF", "atrial fibrillation", True),
        ("PE", "pulmonary embolism", True),
        ("DVT", "deep vein thrombosis", True),
        ("SOB", "shortness of breath", True),
        ("CP", "chest pain", True),
        ("BP", "blood pressure", True),
        ("HR", "heart rate", True),
        ("RR", "respiratory rate", True),
        # Negative cases
        ("STEMI", "NSTEMI", False),
        ("hypertension", "hypotension", False),
        ("hyperglycemia", "hypoglycemia", False),
        ("tachycardia", "bradycardia", False),
    ]

    print("\n=== Medical Terminology Tests ===")
    results = []
    for expected, actual, should_match in test_cases:
        result = comparator.compare(expected, actual)
        matched = result.matched
        confidence = result.confidence

        status = "✓" if matched == should_match else "✗"
        print(
            f"{status} '{expected}' vs '{actual}': {matched} (conf: {confidence:.3f}) [expected: {should_match}]"
        )

        results.append(matched == should_match)

    accuracy = sum(results) / len(results)
    print(f"\nMedical Accuracy: {accuracy:.1%} ({sum(results)}/{len(results)})")

    return accuracy


def test_legal_terminology():
    """Test legal domain vocabulary substitutions."""
    comparator = EmbeddingComparator(threshold=0.80)

    test_cases = [
        # (expected, actual, should_match)
        ("42 USC § 1983", "Section 1983", True),
        ("42 USC § 1983", "42 U.S.C. 1983", True),
        ("habeas corpus", "writ of habeas corpus", True),
        ("pro se", "self-represented", True),
        ("voir dire", "jury selection", True),
        ("prima facie", "at first sight", True),
        ("res judicata", "matter adjudged", True),
        ("stare decisis", "precedent", True),
        ("amicus curiae", "friend of the court", True),
        ("in camera", "in private", True),
        ("ex parte", "one-sided", True),
        ("de novo", "anew", True),
        ("certiorari", "cert", True),
        ("plaintiff", "complainant", True),
        ("defendant", "respondent", True),
        ("tort", "civil wrong", True),
        ("negligence", "breach of duty", True),
        # Negative cases
        ("plaintiff", "defendant", False),
        ("guilty", "not guilty", False),
        ("felony", "misdemeanor", False),
    ]

    print("\n=== Legal Terminology Tests ===")
    results = []
    for expected, actual, should_match in test_cases:
        result = comparator.compare(expected, actual)
        matched = result.matched
        confidence = result.confidence

        status = "✓" if matched == should_match else "✗"
        print(
            f"{status} '{expected}' vs '{actual}': {matched} (conf: {confidence:.3f}) [expected: {should_match}]"
        )

        results.append(matched == should_match)

    accuracy = sum(results) / len(results)
    print(f"\nLegal Accuracy: {accuracy:.1%} ({sum(results)}/{len(results)})")

    return accuracy


if __name__ == "__main__":
    """Run all domain-specific tests."""
    print("=" * 60)
    print("Domain-Specific Terminology Validation")
    print("Testing if embeddings handle domain jargon without fine-tuning")
    print("=" * 60)

    financial_acc = test_financial_terminology()
    medical_acc = test_medical_terminology()
    legal_acc = test_legal_terminology()

    print("\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)
    print(f"Financial: {financial_acc:.1%}")
    print(f"Medical:   {medical_acc:.1%}")
    print(f"Legal:     {legal_acc:.1%}")
    print(f"Average:   {(financial_acc + medical_acc + legal_acc) / 3:.1%}")

    print("\n" + "=" * 60)
    print("DECISION FRAMEWORK")
    print("=" * 60)

    avg_accuracy = (financial_acc + medical_acc + legal_acc) / 3

    if avg_accuracy >= 0.85:
        print("✅ SHIP IT: Accuracy >= 85%")
        print("   Embeddings handle domain terminology well enough.")
        print("   No fine-tuning needed.")
    elif avg_accuracy >= 0.75:
        print("⚠️  CONSIDER TRAINING: Accuracy 75-85%")
        print("   Embeddings work but training could improve 5-10%.")
        print("   Decide based on production requirements.")
    else:
        print("❌ TRAIN: Accuracy < 75%")
        print("   Domain-specific fine-tuning recommended.")
        print("   Embeddings struggle with domain jargon.")

    print("=" * 60)
