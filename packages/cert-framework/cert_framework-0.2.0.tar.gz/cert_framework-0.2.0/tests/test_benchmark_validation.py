"""Benchmark validation using STS-Benchmark dataset.

STS-Benchmark: 8,628 sentence pairs with human similarity judgments (0-5 scale).
Dataset: https://github.com/PhilipMay/stsb-multi-mt

This validates embedding accuracy against real human judgments rather than
hand-crafted examples.

Target: >85% accuracy for shipping without training.
If <85%: Consider domain-specific fine-tuning.
"""

import pytest
from cert.embeddings import EmbeddingComparator
import csv
from pathlib import Path


class TestSTSBenchmarkValidation:
    """Validate EmbeddingComparator accuracy on STS-Benchmark."""

    def setup_method(self):
        """Initialize comparator and load dataset."""
        self.comparator = EmbeddingComparator(threshold=0.75)
        self.dataset_path = Path(__file__).parent / "data" / "sts-benchmark"

    def _download_dataset(self):
        """Download STS-Benchmark if not available.

        Dataset structure:
        - sts-train.csv: 5,749 pairs (training set)
        - sts-dev.csv: 1,500 pairs (development set)
        - sts-test.csv: 1,379 pairs (test set)

        Format: sentence1, sentence2, score
        Score: 0 (no relation) to 5 (semantic equivalence)
        """
        if self.dataset_path.exists():
            return

        # Create data directory
        self.dataset_path.mkdir(parents=True, exist_ok=True)

        print("Downloading STS-Benchmark from Hugging Face...")

        try:
            # Try using datasets library (preferred)
            from datasets import load_dataset

            dataset = load_dataset("mteb/stsbenchmark-sts")

            # Save to CSV files
            for split in ["train", "validation", "test"]:
                output_path = self.dataset_path / (
                    "sts-{}.csv".format("dev" if split == "validation" else split)
                )

                split_data = dataset[split]

                with open(output_path, "w", encoding="utf-8") as f:
                    import csv

                    writer = csv.writer(f, delimiter="\t")

                    for item in split_data:
                        # Format: sentence1, sentence2, score
                        writer.writerow(
                            [item["sentence1"], item["sentence2"], item["score"]]
                        )

                print("Saved {} split to {}".format(split, output_path))

        except ImportError:
            # Fallback: Download from ixa2.si.ehu.es (original source)

            print("datasets library not available, using direct download...")
            print("Please install with: pip install datasets")
            raise ImportError(
                "STS-Benchmark download requires datasets library. "
                "Install with: pip install datasets"
            )

    def _load_split(self, split: str):
        """Load a dataset split.

        Returns:
            List of (sentence1, sentence2, similarity_score) tuples
        """
        path = self.dataset_path / ("sts-" + split + ".csv")
        if not path.exists():
            self._download_dataset()

        pairs = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) >= 3:
                    # Format: sentence1, sentence2, score
                    sentence1 = row[0]
                    sentence2 = row[1]
                    score = float(row[2])
                    pairs.append((sentence1, sentence2, score))

        return pairs

    def _score_to_matched(self, human_score: float, threshold: float = 3.5) -> bool:
        """Convert human similarity score (0-5) to binary match.

        STS-Benchmark uses 0-5 scale:
        - 5: Complete semantic equivalence
        - 4: Mostly equivalent
        - 3: Roughly equivalent
        - 2: Not equivalent but on same topic
        - 1: Not equivalent or on same topic
        - 0: Completely dissimilar

        Args:
            human_score: Human judgment (0-5)
            threshold: Score >= threshold means "matched" (default 3.5)

        Returns:
            True if score >= threshold (semantically equivalent)
        """
        return human_score >= threshold

    def _evaluate_split(self, split: str, sample_size: int = None) -> dict:
        """Evaluate comparator on a dataset split.

        Args:
            split: "train", "dev", or "test"
            sample_size: Optional sample size for quick testing

        Returns:
            Dict with accuracy, precision, recall, F1, and confusion matrix
        """
        pairs = self._load_split(split)

        if sample_size:
            import random

            pairs = random.sample(pairs, min(sample_size, len(pairs)))

        # Evaluate each pair
        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0

        for sentence1, sentence2, human_score in pairs:
            # Get comparator prediction
            result = self.comparator.compare(sentence1, sentence2)
            predicted_match = result.matched

            # Get human judgment
            human_match = self._score_to_matched(human_score)

            # Update confusion matrix
            if predicted_match and human_match:
                true_positives += 1
            elif not predicted_match and not human_match:
                true_negatives += 1
            elif predicted_match and not human_match:
                false_positives += 1
            else:  # not predicted_match and human_match
                false_negatives += 1

        # Calculate metrics
        total = len(pairs)
        accuracy = (true_positives + true_negatives) / total

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "split": split,
            "total": total,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "confusion_matrix": {
                "true_positives": true_positives,
                "true_negatives": true_negatives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
            },
        }

    def test_dev_split_sample(self):
        """Quick validation on 100 samples from dev set."""
        results = self._evaluate_split("dev", sample_size=100)

        print("\n=== STS-Benchmark Dev Split (100 samples) ===")
        print(f"Accuracy: {results['accuracy']:.2%}")
        print(f"Precision: {results['precision']:.2%}")
        print(f"Recall: {results['recall']:.2%}")
        print(f"F1: {results['f1']:.2%}")
        print("Confusion Matrix:")
        print(f"  TP: {results['confusion_matrix']['true_positives']}")
        print(f"  TN: {results['confusion_matrix']['true_negatives']}")
        print(f"  FP: {results['confusion_matrix']['false_positives']}")
        print(f"  FN: {results['confusion_matrix']['false_negatives']}")

        # Quick check: Should be reasonable (>60%)
        assert results["accuracy"] > 0.60, (
            f"Accuracy too low: {results['accuracy']:.2%}"
        )

    @pytest.mark.slow
    def test_full_dev_split(self):
        """Full validation on dev split (1,500 pairs)."""
        results = self._evaluate_split("dev")

        print("\n=== STS-Benchmark Dev Split (Full) ===")
        print(f"Total pairs: {results['total']}")
        print(f"Accuracy: {results['accuracy']:.2%}")
        print(f"Precision: {results['precision']:.2%}")
        print(f"Recall: {results['recall']:.2%}")
        print(f"F1: {results['f1']:.2%}")

        # Target: >85% accuracy for shipping without training
        if results["accuracy"] >= 0.85:
            print("\n✓ Accuracy >= 85%: Embeddings are sufficient, ship it!")
        elif results["accuracy"] >= 0.75:
            print("\n⚠ Accuracy 75-85%: Consider domain-specific training")
        else:
            print("\n✗ Accuracy < 75%: Domain-specific training recommended")

        assert results["accuracy"] > 0.70, (
            f"Accuracy too low: {results['accuracy']:.2%}"
        )

    @pytest.mark.slow
    def test_full_test_split(self):
        """Full validation on test split (1,379 pairs)."""
        results = self._evaluate_split("test")

        print("\n=== STS-Benchmark Test Split (Full) ===")
        print(f"Total pairs: {results['total']}")
        print(f"Accuracy: {results['accuracy']:.2%}")
        print(f"Precision: {results['precision']:.2%}")
        print(f"Recall: {results['recall']:.2%}")
        print(f"F1: {results['f1']:.2%}")

        # Report recommendation
        if results["accuracy"] >= 0.85:
            recommendation = "SHIP: Embeddings sufficient for production"
        elif results["accuracy"] >= 0.75:
            recommendation = "CONSIDER: Training may improve accuracy by 5-10%"
        else:
            recommendation = "TRAIN: Domain-specific fine-tuning recommended"

        print(f"\nRecommendation: {recommendation}")

        assert results["accuracy"] > 0.70, (
            f"Accuracy too low: {results['accuracy']:.2%}"
        )

    def test_threshold_tuning(self):
        """Test different thresholds to find optimal value.

        This helps tune the embedding_threshold parameter for IntelligentComparator.
        """
        # Load all pairs and sample
        pairs = self._load_split("dev")

        # Sample for faster tuning
        import random

        if len(pairs) > 500:
            pairs = random.sample(pairs, 500)

        thresholds = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
        results = []

        print("\n=== Threshold Tuning (500 samples) ===")

        for threshold in thresholds:
            comparator = EmbeddingComparator(threshold=threshold)

            correct = 0
            for sentence1, sentence2, human_score in pairs:
                result = comparator.compare(sentence1, sentence2)
                human_match = self._score_to_matched(human_score)

                if result.matched == human_match:
                    correct += 1

            accuracy = correct / len(pairs)
            results.append((threshold, accuracy))
            print(f"Threshold {threshold:.2f}: {accuracy:.2%}")

        # Find best threshold
        best_threshold, best_accuracy = max(results, key=lambda x: x[1])
        print(f"\nBest threshold: {best_threshold:.2f} ({best_accuracy:.2%})")

        return best_threshold


class TestDomainSpecificValidation:
    """Measure accuracy on domain-specific datasets.

    This measures the "training gap" - how much would fine-tuning help?
    """

    def setup_method(self):
        """Initialize comparator."""
        self.comparator = EmbeddingComparator(threshold=0.75)

    @pytest.mark.skip(reason="FinQA dataset requires separate download")
    def test_finqa_validation(self):
        """Validate on FinQA dataset (financial question answering).

        FinQA: 8,281 question-answer pairs from financial reports.
        Dataset: https://github.com/czyssrs/FinQA

        This tests if embeddings handle financial terminology well.
        """
        # TODO: Download and process FinQA dataset
        # Expected: Lower accuracy than STS-Benchmark (70-80%)
        # Training gap: 10-15% improvement possible
        pass

    @pytest.mark.skip(reason="MedQA dataset requires separate download")
    def test_medqa_validation(self):
        """Validate on MedQA dataset (medical question answering).

        MedQA: 12,723 USMLE-style questions.
        Dataset: https://github.com/jind11/MedQA

        This tests if embeddings handle medical terminology well.
        """
        # TODO: Download and process MedQA dataset
        # Expected: Lower accuracy than STS-Benchmark (65-75%)
        # Training gap: 15-20% improvement possible
        pass

    @pytest.mark.skip(reason="LegalBench dataset requires separate download")
    def test_legalbench_validation(self):
        """Validate on LegalBench dataset (legal reasoning).

        LegalBench: 162 tasks covering legal reasoning.
        Dataset: https://github.com/HazyResearch/legalbench

        This tests if embeddings handle legal citations well.
        """
        # TODO: Download and process LegalBench dataset
        # Expected: Lower accuracy than STS-Benchmark (60-70%)
        # Training gap: 20-25% improvement possible
        pass


if __name__ == "__main__":
    """Run quick validation for manual testing."""
    import sys

    print("Running quick STS-Benchmark validation...")

    validator = TestSTSBenchmarkValidation()
    validator.setup_method()

    try:
        # Run quick test
        validator.test_dev_split_sample()

        # Run threshold tuning
        best_threshold = validator.test_threshold_tuning()

        print(f"\n{'=' * 60}")
        print("Quick validation complete!")
        print(f"Recommended threshold: {best_threshold:.2f}")
        print("\nTo run full validation:")
        print("  pytest -v -m slow tests/test_benchmark_validation.py")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
