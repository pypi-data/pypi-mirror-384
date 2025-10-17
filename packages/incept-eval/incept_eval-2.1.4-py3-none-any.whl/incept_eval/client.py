"""Local evaluator client for Incept"""
from .evaluator import universal_unified_benchmark, UniversalEvaluationRequest

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

        # Convert Pydantic model back to dict
        return response.model_dump()
