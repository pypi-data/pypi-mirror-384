"""
DSPy Assertions and Auto-Healing

Enforce contracts with dspy.Assert and auto-heal on failures by:
- Lowering temperature
- Increasing k (retrieval)
- Switching model arms
- Retrying with adjusted parameters
"""

import logging
from typing import Any, Optional, Callable
from dataclasses import dataclass

import dspy

logger = logging.getLogger(__name__)


@dataclass
class HealingConfig:
    """Configuration for auto-healing retries"""
    max_retries: int = 3
    temperature_decay: float = 0.5  # Multiply temperature by this on each retry
    k_multiplier: float = 1.5       # Multiply k by this on each retry
    max_k: int = 48                # Maximum k value
    fallback_models: list[str] = None  # Models to try on failure (not used with single Falcon model)

    def __post_init__(self):
        if self.fallback_models is None:
            # No fallback models - using single Falcon model
            self.fallback_models = []


def assert_citations(output: Any, min_citations: int = 1) -> bool:
    """Assert output has sufficient citations"""
    citations = getattr(output, 'citations', []) or []
    return len(citations) >= min_citations


def assert_confidence(output: Any, min_confidence: float = 0.5) -> bool:
    """Assert output meets minimum confidence threshold"""
    confidence = getattr(output, 'confidence', 0.0)
    return confidence >= min_confidence


def assert_answer_present(output: Any) -> bool:
    """Assert output has a non-empty answer"""
    answer = getattr(output, 'answer', '') or ''
    return len(answer.strip()) > 0


def assert_no_hallucination_markers(output: Any) -> bool:
    """Assert answer doesn't contain hallucination markers"""
    answer = getattr(output, 'answer', '') or ''
    markers = ['hallucin', 'unknown', 'insufficient evidence', 'cannot determine']
    return not any(marker in answer.lower() for marker in markers)


def assert_grade_appropriate(output: Any, grade: int) -> bool:
    """Assert output is grade appropriate"""
    # Check if output has grade_appropriate flag
    if hasattr(output, 'grade_appropriate'):
        return output.grade_appropriate

    # Check if output has grade_level_score
    if hasattr(output, 'grade_level_score'):
        # Score should be >= 7 for appropriate
        return output.grade_level_score >= 7

    # Default to true if no grade checking available
    return True


def assert_json_valid(output: Any, required_fields: list[str]) -> bool:
    """Assert output has required JSON fields"""
    for field in required_fields:
        if not hasattr(output, field):
            return False
        val = getattr(output, field)
        if val is None or (isinstance(val, str) and not val.strip()):
            return False
    return True


def with_auto_healing(
    func: Callable,
    assertions: list[Callable[[Any], bool]],
    config: Optional[HealingConfig] = None
) -> Callable:
    """
    Decorator to add auto-healing with assertions.

    Args:
        func: Function to wrap (should return DSPy output)
        assertions: List of assertion functions to validate output
        config: Healing configuration

    Returns:
        Wrapped function with auto-healing
    """
    config = config or HealingConfig()

    def wrapper(*args, **kwargs):
        temperature = kwargs.get('temperature', 0.3)
        k = kwargs.get('k', 12)
        model_idx = 0

        for attempt in range(config.max_retries):
            try:
                # Execute function
                output = func(*args, **kwargs)

                # Run assertions
                all_passed = True
                for assertion in assertions:
                    try:
                        if not assertion(output):
                            all_passed = False
                            logger.warning(f"Assertion failed: {assertion.__name__}")
                            break
                    except Exception as e:
                        logger.warning(f"Assertion {assertion.__name__} error: {e}")
                        all_passed = False
                        break

                if all_passed:
                    return output

                # Auto-heal: adjust parameters for retry
                if attempt < config.max_retries - 1:
                    # Lower temperature
                    temperature *= config.temperature_decay
                    kwargs['temperature'] = max(0.0, temperature)
                    logger.info(f"Auto-heal: lowering temperature to {temperature:.3f}")

                    # Increase k if retrieval-based
                    if 'k' in kwargs:
                        k = min(int(k * config.k_multiplier), config.max_k)
                        kwargs['k'] = k
                        logger.info(f"Auto-heal: increasing k to {k}")

                    # Try fallback model
                    if model_idx < len(config.fallback_models):
                        fallback_model = config.fallback_models[model_idx]
                        model_idx += 1
                        # Note: Model switching would need to be implemented
                        # in the calling context (e.g., via dspy.context)
                        logger.info(f"Auto-heal: would switch to {fallback_model}")

            except Exception as e:
                logger.error(f"Auto-heal attempt {attempt + 1} failed: {e}")
                if attempt == config.max_retries - 1:
                    raise

        # All retries exhausted
        logger.error(f"Auto-heal exhausted {config.max_retries} retries")
        raise ValueError("Auto-healing failed: all assertions failed after max retries")

    return wrapper


class AssertionValidator:
    """Validation helper that runs assertions and provides feedback"""

    def __init__(self):
        self.validators = {
            'citations': assert_citations,
            'confidence': assert_confidence,
            'answer_present': assert_answer_present,
            'no_hallucination': assert_no_hallucination_markers,
            'grade_appropriate': assert_grade_appropriate
        }

    def validate(self, output: Any, checks: list[str], **kwargs) -> tuple[bool, list[str]]:
        """
        Run specified validation checks on output.

        Args:
            output: DSPy output to validate
            checks: List of check names to run
            **kwargs: Additional arguments for validators (e.g., min_confidence=0.7)

        Returns:
            (all_passed, failed_checks)
        """
        failed_checks = []

        for check in checks:
            if check not in self.validators:
                logger.warning(f"Unknown validation check: {check}")
                continue

            try:
                validator = self.validators[check]

                # Check if validator needs kwargs
                import inspect
                sig = inspect.signature(validator)
                if len(sig.parameters) > 1:
                    # Pass relevant kwargs
                    if check == 'citations':
                        result = validator(output, kwargs.get('min_citations', 1))
                    elif check == 'confidence':
                        result = validator(output, kwargs.get('min_confidence', 0.5))
                    elif check == 'grade_appropriate':
                        result = validator(output, kwargs.get('grade', 1))
                    else:
                        result = validator(output)
                else:
                    result = validator(output)

                if not result:
                    failed_checks.append(check)

            except Exception as e:
                logger.error(f"Validation check {check} failed with error: {e}")
                failed_checks.append(check)

        return len(failed_checks) == 0, failed_checks

    def add_validator(self, name: str, func: Callable[[Any], bool]):
        """Add custom validator"""
        self.validators[name] = func


# Global validator instance
_validator = AssertionValidator()


def validate_output(output: Any, checks: list[str], **kwargs) -> tuple[bool, list[str]]:
    """Validate DSPy output with specified checks"""
    return _validator.validate(output, checks, **kwargs)
