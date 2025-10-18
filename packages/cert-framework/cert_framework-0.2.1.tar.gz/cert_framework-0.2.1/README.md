# CERT Framework

Test your LLM applications for reliability. Catch hallucinations, inconsistencies, and regressions before they reach production.

## Install
```bash
pip install cert-framework
```

## Quick Start
```python
from cert import compare

# Test if two LLM responses are semantically equivalent
expected = "Revenue increased 15% year-over-year"
actual = "Sales grew by fifteen percent compared to last year"

result = compare(expected, actual)
print(result.matched)      # True
print(result.confidence)   # 0.89
```

## What It Does

CERT validates LLM outputs using semantic comparison - meaning over keywords. It detects when responses are equivalent despite different wording, and flags genuine differences that indicate hallucinations or drift.

**Validated accuracy**: 87.6% on STS-Benchmark (8,628 human-annotated test pairs)

## Core Use Cases

### 1. Test Response Consistency

Verify your LLM gives consistent answers to the same question:
```python
from cert import compare

responses = [
    "Refunds available within 30 days",
    "Full refund if requested in 30-day window", 
    "90-day return policy"  # ← Inconsistent!
]

baseline = responses[0]
for response in responses[1:]:
    result = compare(baseline, response)
    if not result.matched:
        print(f"Inconsistency detected: {response}")
```

### 2. Catch Regressions

Test if model upgrades break existing behavior:
```python
from cert import compare

# Expected output from v1
expected = "Contact support@company.com for billing issues"

# Actual output from v2
actual = llm_v2.query("How do I contact billing?")

result = compare(expected, actual)
assert result.matched, f"Regression: {actual}"
```

### 3. Validate RAG Retrieval

Verify retrieval systems return semantically relevant results:
```python
from cert import compare

query = "What are the side effects of aspirin?"
expected_content = "Common side effects include stomach irritation..."

retrieved = rag_system.retrieve(query)
result = compare(expected_content, retrieved[0].content)

assert result.matched, "Retrieved irrelevant content"
```

## How It Works

Uses `all-mpnet-base-v2` sentence transformers to create semantic embeddings. Texts are compared via cosine similarity with a default threshold of 0.80.

**First call downloads the model (~420MB, one-time)**. Subsequent calls are fast (~50-100ms).

## Configuration
```python
# Adjust threshold per comparison
result = compare(text1, text2, threshold=0.90)  # Stricter

# Or configure globally
from cert import EmbeddingComparator
comparator = EmbeddingComparator(threshold=0.85)
result = comparator.compare(text1, text2)
```

## pytest Integration
```python
import pytest
from cert import compare

def test_llm_consistency():
    response1 = llm.query("What is our return policy?")
    response2 = llm.query("What is our return policy?")
    
    result = compare(response1, response2)
    assert result.matched, f"Inconsistent responses: {result.confidence}"
```

## Limitations

- **Short texts** (1-2 words): Accuracy drops to ~70%
- **Negations**: "revenue up" vs "revenue down" may score high similarity
- **Technical jargon**: Uncommon terminology may need domain fine-tuning

For general text, financial terminology, and medical content: 85%+ accuracy.

## Requirements

- Python 3.8+
- Works on CPU (no GPU required)
- ~500MB disk space for model

## License

MIT

## Links

- GitHub: https://github.com/Javihaus/cert-framework
- Issues: https://github.com/Javihaus/cert-framework/issues
- PyPI: https://pypi.org/project/cert-framework/
