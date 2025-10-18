"""Local evaluator client for Incept"""
from .evaluator import universal_unified_benchmark, benchmark_parallel, UniversalEvaluationRequest

class InceptClient:
    def __init__(self, api_key=None, base_url=None, timeout=600):
        """
        Local evaluator client - runs universal_unified_benchmark directly.

        Args:
            api_key: Not used (kept for backward compatibility)
            base_url: Not used (kept for backward compatibility)
            timeout: Not used (kept for backward compatibility)
        """
        self.timeout = timeout

    def evaluate_dict(self, data):
        """
        Evaluate questions using local universal_unified_benchmark function.

        Args:
            data: Dictionary containing the evaluation request

        Returns:
            Dictionary with evaluation results
        """
        # Convert dict to Pydantic model
        request = UniversalEvaluationRequest(**data)

        # Run evaluation
        response = universal_unified_benchmark(request)

        # Convert Pydantic model back to dict, excluding None values
        return response.model_dump(exclude_none=True)

    def benchmark(self, data, max_workers=100):
        """
        Benchmark mode: Process many questions in parallel.

        Args:
            data: Dictionary containing the evaluation request
            max_workers: Number of parallel workers (default: 100)

        Returns:
            Dictionary with benchmark results including scores and failed IDs
        """
        # Convert dict to Pydantic model
        request = UniversalEvaluationRequest(**data)

        # Run benchmark
        result = benchmark_parallel(request, max_workers=max_workers)

        return result
