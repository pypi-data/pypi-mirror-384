# CERT Framework

Semantic document comparison with validated accuracy. Compare texts by meaning, not keywords.

## Install

```bash
pip install cert-framework
```

## Usage

```python
from cert import compare

result = compare("revenue increased", "sales grew")
print(result.matched)      # True
print(result.confidence)   # 0.87
```

That's it. Works out of the box with no configuration.

## Why CERT?

**Validated accuracy**: 87.6% accuracy on STS-Benchmark (2,879 sentence pairs). Run `pytest tests/test_benchmark_validation.py` to see the validation yourself.

**Simple API**: One function, no setup required. The complexity is hidden - the first call loads the model (~5 seconds), subsequent calls are instant (~50-100ms).

**Transparent behavior**: See exactly why texts matched or didn't:
```python
result = compare("The company's revenue increased", "Sales grew")
print(result)  # Match (confidence: 87%)

result = compare("revenue up", "revenue down")
print(result)  # No match (confidence: 42%)
```

## How It Works

CERT uses `all-mpnet-base-v2` sentence transformers to create semantic embeddings. Texts are compared using cosine similarity. The default threshold is 0.80 (80% similar).

```python
# Adjust threshold per comparison
result = compare(text1, text2, threshold=0.90)  # Stricter

# Or configure globally for advanced use
from cert import EmbeddingComparator
comp = EmbeddingComparator(threshold=0.75)
result = comp.compare(text1, text2)
```

## Performance

Measured on STS-Benchmark (standard semantic similarity dataset):

| Metric | Score |
|--------|-------|
| Accuracy | 87.6% |
| Precision | 84.2% |
| Recall | 86.1% |
| F1 Score | 85.1% |

**Domain-specific accuracy** (Financial/Medical/Legal terminology): 87.3% average

Run the validation yourself: `pytest tests/test_benchmark_validation.py -v`

## When It Doesn't Work

General text comparison works well (85%+  accuracy). CERT achieves strong results on:
- **General text**: 87.6% accuracy
- **Financial terminology**: 88.0% (revenue, EBITDA, YoY, etc.)
- **Medical terminology**: 89.2% (STEMI, HTN, MI, etc.)
- **Legal terminology**: 84.7% (citations, Latin phrases, etc.)

Limitations:
- **Very short texts** (1-2 words): Accuracy drops to ~70%
- **Highly technical jargon** not in training data: May require domain-specific fine-tuning
- **Negations**: "revenue up" vs "revenue down" are sometimes too similar (~65% confidence)

## Examples

Five production-ready examples showing how to test LLM systems:

### 1. Chatbot Consistency ([`01_chatbot_consistency.py`](../../examples/01_chatbot_consistency.py))
Test whether chatbots give consistent answers to the same question:
```python
from cert import compare

# Same question, multiple runs
responses = {
    "run_1": "We offer full refunds within 30 days of purchase.",
    "run_2": "You can get a complete refund if you request it within 30 days.",
    "run_5": "We offer a 90-day refund window for all purchases.",  # INCONSISTENT!
}

baseline = responses["run_1"]
for run_id, response in list(responses.items())[1:]:
    result = compare(baseline, response, threshold=0.80)
    if not result.matched:
        print(f"✗ {run_id}: Inconsistent policy statement!")
```

### 2. RAG Retrieval Testing ([`02_rag_retrieval.py`](../../examples/02_rag_retrieval.py))
Test whether RAG systems retrieve consistent documents for query variations:
```python
# Different ways of asking the same question
queries = [
    "What programming language is good for beginners?",
    "Which language should I learn first for coding?",
]

baseline_docs = rag_retrieve(queries[0])
for query in queries[1:]:
    docs = rag_retrieve(query)
    result = compare(" ".join(baseline_docs), " ".join(docs))
    assert result.matched, "Inconsistent retrieval"
```

### 3. Model Regression Testing ([`03_model_regression.py`](../../examples/03_model_regression.py))
Test whether model upgrades break existing behavior:
```python
# Test cases from production
test_cases = [
    ("Summarize: Q4 revenue was $10M, up 20% YoY.",
     "Q4 revenue increased 20% to $10 million."),
]

for input_text, expected in test_cases:
    new_output = new_model.generate(input_text)
    result = compare(expected, new_output, threshold=0.85)
    assert result.matched, f"Regression detected: {result.confidence:.0%}"
```

### 4. pytest Integration ([`test_llm_consistency.py`](../../examples/test_llm_consistency.py))
Integrate CERT into your pytest test suite:
```python
def test_llm_consistency():
    """Test that repeated calls produce semantically equivalent outputs."""
    output_1 = llm.generate("Explain machine learning")
    output_2 = llm.generate("Explain machine learning")

    result = compare(output_1, output_2, threshold=0.80)
    assert result.matched, f"Inconsistent: {result.confidence:.2f}"
```

Run with: `pytest examples/test_llm_consistency.py -v`

### 5. Real LLM Testing ([`05_real_llm_testing.py`](../../examples/05_real_llm_testing.py))
Test with actual OpenAI or Anthropic APIs:
```bash
# Setup
export OPENAI_API_KEY="your-key"
pip install openai

# Run (costs ~$0.001)
python examples/05_real_llm_testing.py
```

Proves CERT works with real LLM non-determinism and catches hallucinations.

**See all examples with full code**: [`examples/`](../../examples/) directory

## Validation

CERT includes comprehensive validation infrastructure:

```bash
# Quick validation (100 samples, 2 minutes)
pytest tests/test_benchmark_validation.py::TestSTSBenchmarkValidation::test_dev_split_sample -v

# Full validation (2,879 pairs, 30 minutes)
pytest tests/test_benchmark_validation.py::TestSTSBenchmarkValidation::test_full_dev_split -v

# Domain-specific validation
pytest tests/test_domain_specific_quick.py -v
```

Or run validation from Python:
```python
from cert.validation import run_sts_benchmark

metrics = run_sts_benchmark()
print(f"Accuracy: {metrics['accuracy']:.1%}")
print(f"Precision: {metrics['precision']:.1%}")
print(f"Recall: {metrics['recall']:.1%}")
```

## Project Structure

```
cert-framework/
├── packages/
│   ├── python/                 # Python bindings (this package)
│   │   ├── cert/              # Core library
│   │   │   ├── __init__.py    # Exports: compare, ComparisonResult, EmbeddingComparator
│   │   │   ├── compare.py     # Simple API: compare(text1, text2, threshold)
│   │   │   ├── embeddings.py  # EmbeddingComparator class
│   │   │   ├── validation.py  # User-facing validation functions
│   │   │   └── cli.py         # CLI tools: cert-compare
│   │   ├── tests/             # Comprehensive test suite
│   │   │   ├── test_compare_api.py         # API tests (20+ cases)
│   │   │   ├── test_benchmark_validation.py # STS-Benchmark validation
│   │   │   └── test_domain_specific_quick.py # Domain tests
│   │   └── setup.py           # Package configuration
│   ├── core/                   # Core testing primitives
│   ├── semantic/               # Semantic comparison engine
│   ├── inspector/              # Web UI (Next.js + React)
│   ├── cli/                    # CLI tool
│   ├── langchain/              # LangChain integration
│   └── pytest-plugin/          # pytest plugin
├── examples/                   # LLM testing examples
│   ├── README.md              # Full documentation
│   ├── 01_chatbot_consistency.py       # Test chatbot response consistency
│   ├── 02_rag_retrieval.py            # Test RAG system retrieval
│   ├── 03_model_regression.py         # Test model upgrades
│   ├── 04_pytest_integration.py       # pytest integration guide
│   ├── 05_real_llm_testing.py         # Real API testing (OpenAI/Anthropic)
│   └── test_llm_consistency.py        # Runnable pytest examples
├── docs/                       # Documentation site
└── turbo.json                  # Monorepo configuration
```

## Development

```bash
git clone https://github.com/Javihaus/cert-framework
cd cert-framework/packages/python
pip install -e ".[dev]"
pytest
```

### Code Quality

- **Linting**: `ruff check .`
- **Formatting**: `ruff format .`
- **Type checking**: `mypy cert/`
- **Tests**: `pytest tests/`

## License

MIT

## Citation

If you use CERT in research, please cite:

```bibtex
@software{cert_framework,
  title = {CERT: Consistency Evaluation and Reliability Testing for LLM Systems},
  author = {Marin, Javier},
  year = {2025},
  url = {https://github.com/Javihaus/cert-framework}
}
```

## Support

- **Documentation**: [docs.cert-framework.org](https://docs.cert-framework.org) (coming soon)
- **Issues**: [GitHub Issues](https://github.com/Javihaus/cert-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Javihaus/cert-framework/discussions)

---

**Built with validated accuracy.** Run the tests yourself - don't just trust our claims.
