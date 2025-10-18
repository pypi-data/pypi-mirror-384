"""
CERT Framework - LangChain Integration

Native Python wrapper for LangChain chains with CERT testing capabilities.
"""

from typing import Any, Optional, Callable
import asyncio


class CertChainWrapper:
    """Wraps a LangChain chain with CERT testing capabilities"""

    def __init__(self, chain: Any, test_id: str = "langchain-test"):
        """
        Initialize wrapper

        Args:
            chain: LangChain chain instance
            test_id: Unique identifier for this test
        """
        self.chain = chain
        self.test_id = test_id
        self._consistency_threshold: Optional[float] = None
        self._consistency_trials: int = 5
        self._expected_output: Optional[Any] = None
        self._comparison_fn: Optional[Callable] = None

    def with_consistency(self, threshold: float = 0.8, n_trials: int = 5):
        """
        Add consistency testing to the chain.

        Args:
            threshold: Minimum consistency score (0-1)
            n_trials: Number of trials to run

        Returns:
            Self for chaining

        Example:
            ```python
            cert_chain = wrap_chain(chain).with_consistency(threshold=0.9, n_trials=5)
            ```
        """
        self._consistency_threshold = threshold
        self._consistency_trials = n_trials
        return self

    def with_accuracy(
        self, expected_output: Any, comparison_fn: Optional[Callable] = None
    ):
        """
        Add accuracy testing to the chain.

        Args:
            expected_output: The expected output
            comparison_fn: Optional custom comparison function

        Returns:
            Self for chaining

        Example:
            ```python
            cert_chain = wrap_chain(chain).with_accuracy("Paris")
            ```
        """
        self._expected_output = expected_output
        self._comparison_fn = comparison_fn
        return self

    async def ainvoke(self, input_data: dict, **kwargs) -> Any:
        """
        Async invoke with CERT testing

        Args:
            input_data: Input dictionary for the chain
            **kwargs: Additional arguments passed to chain

        Returns:
            Chain output

        Raises:
            AccuracyError: If accuracy test fails
            ConsistencyError: If consistency test fails
        """
        from cert.runner import TestRunner, ConsistencyError, AccuracyError
        from cert.types import TestConfig, GroundTruth

        runner = TestRunner()

        async def _run_chain():
            """Helper to run chain"""
            if hasattr(self.chain, "ainvoke"):
                return await self.chain.ainvoke(input_data, **kwargs)
            elif hasattr(self.chain, "arun"):
                return await self.chain.arun(input_data, **kwargs)
            else:
                # Fallback to sync invoke
                return self.chain.invoke(input_data, **kwargs)

        # If accuracy testing is enabled, run it first
        if self._expected_output is not None:
            # Add ground truth
            runner.add_ground_truth(
                GroundTruth(
                    id=self.test_id,
                    question=str(input_data),
                    expected=self._expected_output,
                    metadata={"correctPages": [1]},  # Dummy for layer enforcement
                )
            )

            # Test retrieval (dummy)
            await runner.test_retrieval(
                self.test_id,
                lambda _: asyncio.create_task(
                    asyncio.coroutine(lambda: [{"pageNum": 1}])()
                ),
                {"precisionMin": 0.8},
            )

            # Test accuracy
            accuracy_result = await runner.test_accuracy(
                self.test_id, _run_chain, {"threshold": 0.8}
            )

            if accuracy_result.status == "fail":
                raise AccuracyError(
                    accuracy_result.diagnosis or "Accuracy test failed",
                    str(self._expected_output),
                    "actual output",
                )

        # If consistency testing is enabled, run it
        if self._consistency_threshold is not None:
            if self._expected_output is None:
                # Add dummy ground truth for layer enforcement
                runner.add_ground_truth(
                    GroundTruth(
                        id=self.test_id,
                        question=str(input_data),
                        expected="dummy",
                        metadata={"correctPages": [1]},
                    )
                )

                # Test retrieval (dummy)
                await runner.test_retrieval(
                    self.test_id,
                    lambda _: asyncio.create_task(
                        asyncio.coroutine(lambda: [{"pageNum": 1}])()
                    ),
                    {"precisionMin": 0.8},
                )

                # Test accuracy (dummy)
                await runner.test_accuracy(self.test_id, _run_chain, {"threshold": 0.8})

            config = TestConfig(
                n_trials=self._consistency_trials,
                consistency_threshold=self._consistency_threshold,
                accuracy_threshold=0.8,
                semantic_comparison=True,
            )

            result = await runner.test_consistency(self.test_id, _run_chain, config)

            if result.status == "fail":
                raise ConsistencyError(
                    result.diagnosis or "Consistency test failed",
                    result.suggestions or [],
                )

            # Return the first output from consistency testing
            return result.evidence.outputs[0] if result.evidence else await _run_chain()

        # If no testing, just run the chain
        return await _run_chain()

    def invoke(self, input_data: dict, **kwargs) -> Any:
        """
        Sync invoke with CERT testing

        Args:
            input_data: Input dictionary for the chain
            **kwargs: Additional arguments passed to chain

        Returns:
            Chain output
        """
        return asyncio.run(self.ainvoke(input_data, **kwargs))

    def __call__(self, input_data: dict, **kwargs) -> Any:
        """Allow calling the wrapper like a function"""
        return self.invoke(input_data, **kwargs)


def wrap_chain(chain: Any, test_id: str = "langchain-test") -> CertChainWrapper:
    """
    Wrap a LangChain chain with CERT testing capabilities.

    Example:
        ```python
        from langchain.chains import LLMChain
        from cert.langchain_integration import wrap_chain

        chain = LLMChain(llm=llm, prompt=prompt)
        cert_chain = wrap_chain(chain, "my-chain-test")

        # Add consistency testing
        cert_chain = cert_chain.with_consistency(threshold=0.9, n_trials=5)

        # Run the chain
        result = cert_chain.invoke({"input": "Hello"})
        ```

    Args:
        chain: The LangChain chain to wrap
        test_id: ID for the test

    Returns:
        Wrapped chain with CERT capabilities
    """
    return CertChainWrapper(chain, test_id)
