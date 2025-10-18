"""Consistency measurement and analysis."""

import asyncio
import json
from typing import Any, Callable, List, Set
from .types import ConsistencyResult, TestConfig


async def measure_consistency(
    fn: Callable[[], Any], config: TestConfig
) -> ConsistencyResult:
    """
    Measure consistency by running a function multiple times.

    Args:
        fn: Async function to test for consistency
        config: Test configuration

    Returns:
        ConsistencyResult with metrics and evidence
    """
    outputs: List[Any] = []

    # Run trials
    for _ in range(config.n_trials):
        try:
            # Add timeout
            result = await asyncio.wait_for(
                fn() if asyncio.iscoroutinefunction(fn) else asyncio.to_thread(fn),
                timeout=config.timeout / 1000,
            )
            outputs.append(result)
        except asyncio.TimeoutError:
            outputs.append({"error": "timeout"})
        except Exception as e:
            outputs.append({"error": str(e)})

    # Calculate uniqueness
    unique_outputs: Set[str] = set()
    for output in outputs:
        serialized = json.dumps(output, sort_keys=True, default=str)
        unique_outputs.add(serialized)

    unique_count = len(unique_outputs)

    # Calculate consistency score
    consistency = 1.0 - (unique_count - 1) / max(config.n_trials, 1)

    # Select evidence examples
    evidence = list(unique_outputs)[:5]  # First 5 unique outputs

    return ConsistencyResult(
        consistency=consistency,
        outputs=outputs,
        unique_count=unique_count,
        evidence=evidence,
    )


def autodiagnose_variance(result: ConsistencyResult) -> str:
    """
    Automatically diagnose the cause of variance in outputs.

    Args:
        result: ConsistencyResult to analyze

    Returns:
        Diagnostic message
    """
    unique_count = result.unique_count
    total = len(result.outputs)

    if unique_count == total:
        return (
            f"High variance: All {total} outputs were unique. "
            "Likely causes: high temperature, non-deterministic retrieval, or ambiguous prompt."
        )
    elif unique_count > total * 0.5:
        return (
            f"Moderate variance: {unique_count}/{total} unique outputs. "
            "Consider reducing temperature or checking for non-deterministic components."
        )
    else:
        return (
            f"Low variance: {unique_count}/{total} unique outputs. "
            "Outputs are mostly consistent but have occasional variations."
        )


def select_evidence(outputs: List[Any], unique_outputs: Set[str]) -> List[str]:
    """
    Select representative examples from outputs.

    Args:
        outputs: All outputs from trials
        unique_outputs: Set of unique serialized outputs

    Returns:
        List of example strings
    """
    examples: List[str] = []
    seen: Set[str] = set()

    for output in outputs:
        serialized = json.dumps(output, sort_keys=True, default=str)
        if serialized not in seen:
            # Truncate long outputs
            display = str(output)
            if len(display) > 200:
                display = display[:197] + "..."
            examples.append(display)
            seen.add(serialized)

            if len(examples) >= 5:
                break

    return examples
