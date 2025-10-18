"""Validation tools for measuring comparison accuracy.

This module surfaces the validation infrastructure as a user-facing feature,
allowing users to verify CERT's accuracy claims themselves.
"""

from typing import Dict, Any
from pathlib import Path


def run_sts_benchmark() -> Dict[str, Any]:
    """Run STS-Benchmark validation and return metrics.

    This runs the complete STS-Benchmark validation (2,879 sentence pairs)
    and returns comprehensive accuracy metrics. This takes approximately
    30-45 minutes to complete.

    Returns:
        Dictionary with accuracy, precision, recall, F1 scores

    Example:
        >>> from cert.validation import run_sts_benchmark
        >>> metrics = run_sts_benchmark()
        >>> print(f"Accuracy: {metrics['accuracy']:.1%}")
        Accuracy: 87.6%

    Note:
        This requires the datasets library: pip install datasets
    """
    # Import validation infrastructure
    import sys

    # Add package root to path to import tests
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from tests.test_benchmark_validation import TestSTSBenchmarkValidation

    validator = TestSTSBenchmarkValidation()
    validator.setup_method()

    print("Running STS-Benchmark validation...")
    print("This will take 30-45 minutes. Get some coffee! ☕")
    print()

    # Run dev split
    print("Evaluating development split (1,500 pairs)...")
    dev_results = validator._evaluate_split("dev")

    # Run test split
    print("Evaluating test split (1,379 pairs)...")
    test_results = validator._evaluate_split("test")

    # Combine results
    combined = {
        "accuracy": (dev_results["accuracy"] + test_results["accuracy"]) / 2,
        "precision": (dev_results["precision"] + test_results["precision"]) / 2,
        "recall": (dev_results["recall"] + test_results["recall"]) / 2,
        "f1": (dev_results["f1"] + test_results["f1"]) / 2,
        "dev_split": dev_results,
        "test_split": test_results,
    }

    print()
    print("=" * 60)
    print("STS-BENCHMARK VALIDATION RESULTS")
    print("=" * 60)
    print(f"Accuracy:  {combined['accuracy']:.1%}")
    print(f"Precision: {combined['precision']:.1%}")
    print(f"Recall:    {combined['recall']:.1%}")
    print(f"F1 Score:  {combined['f1']:.1%}")
    print("=" * 60)

    return combined


def run_domain_validation() -> Dict[str, Any]:
    """Run domain-specific validation (Financial, Medical, Legal).

    This runs validation on specialized terminology across three domains:
    - Financial: revenue, EBITDA, YoY, etc.
    - Medical: STEMI, HTN, MI, etc.
    - Legal: citations, Latin phrases, etc.

    Returns:
        Dictionary with accuracy per domain

    Example:
        >>> from cert.validation import run_domain_validation
        >>> metrics = run_domain_validation()
        >>> print(f"Financial: {metrics['financial']:.1%}")
        Financial: 88.0%

    Note:
        This is much faster than STS-Benchmark (~5-10 minutes total)
    """
    import sys
    from pathlib import Path

    # Add package root to path
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from tests.test_domain_specific_quick import (
        test_financial_terminology,
        test_medical_terminology,
        test_legal_terminology,
    )

    print("Running domain-specific validation...")
    print()

    financial_acc = test_financial_terminology()
    medical_acc = test_medical_terminology()
    legal_acc = test_legal_terminology()

    results = {
        "financial": financial_acc,
        "medical": medical_acc,
        "legal": legal_acc,
        "average": (financial_acc + medical_acc + legal_acc) / 3,
    }

    print()
    print("=" * 60)
    print("DOMAIN-SPECIFIC VALIDATION RESULTS")
    print("=" * 60)
    print(f"Financial: {results['financial']:.1%}")
    print(f"Medical:   {results['medical']:.1%}")
    print(f"Legal:     {results['legal']:.1%}")
    print(f"Average:   {results['average']:.1%}")
    print("=" * 60)

    return results


def quick_validation(sample_size: int = 100) -> Dict[str, Any]:
    """Run quick validation on a sample of STS-Benchmark.

    This is useful for rapid testing during development. Completes in ~2 minutes.

    Args:
        sample_size: Number of pairs to sample (default: 100)

    Returns:
        Dictionary with accuracy metrics

    Example:
        >>> from cert.validation import quick_validation
        >>> metrics = quick_validation(sample_size=100)
        >>> print(f"Accuracy: {metrics['accuracy']:.1%}")
        Accuracy: 86.0%
    """
    import sys
    from pathlib import Path

    # Add package root to path
    package_root = Path(__file__).parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from tests.test_benchmark_validation import TestSTSBenchmarkValidation

    validator = TestSTSBenchmarkValidation()
    validator.setup_method()

    print(f"Running quick validation ({sample_size} samples)...")
    results = validator._evaluate_split("dev", sample_size=sample_size)

    print()
    print("=" * 60)
    print(f"QUICK VALIDATION RESULTS ({sample_size} samples)")
    print("=" * 60)
    print(f"Accuracy:  {results['accuracy']:.1%}")
    print(f"Precision: {results['precision']:.1%}")
    print(f"Recall:    {results['recall']:.1%}")
    print(f"F1 Score:  {results['f1']:.1%}")
    print("=" * 60)
    print()
    print("Note: This is a sample. Run run_sts_benchmark() for full validation.")

    return results


if __name__ == "__main__":
    """Command-line interface for validation."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_validation()
    elif len(sys.argv) > 1 and sys.argv[1] == "domain":
        run_domain_validation()
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        run_sts_benchmark()
    else:
        print("CERT Validation Tool")
        print()
        print("Usage:")
        print("  python -m cert.validation quick   # Quick test (100 samples, 2 min)")
        print("  python -m cert.validation domain  # Domain-specific (5-10 min)")
        print("  python -m cert.validation full    # Full STS-Benchmark (30-45 min)")
        print()
        print("Or use from Python:")
        print("  from cert.validation import quick_validation")
        print("  metrics = quick_validation()")
        sys.exit(1)
