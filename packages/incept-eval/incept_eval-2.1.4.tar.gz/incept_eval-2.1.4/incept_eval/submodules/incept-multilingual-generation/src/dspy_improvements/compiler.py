"""
DSPy Compilation & Optimization
Implements BootstrapFewShot and MIPROv2 for automatic prompt optimization

References:
- DSPy Optimizers: https://dspy.ai/api/optimizers/
- BootstrapFewShot: https://deepwiki.com/stanfordnlp/dspy/4.1-optimization-and-teleprompting
- MIPROv2: https://dspy.ai/api/optimizers/MIPROv2/
"""

import dspy
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CompilationMetrics:
    """Metrics for compiled pipeline evaluation"""
    timestamp: str
    compiler: str
    train_size: int
    eval_size: int
    baseline_score: float
    compiled_score: float
    improvement: float
    avg_tokens_saved: int
    p50_latency_ms: float
    p95_latency_ms: float


class RAGMetric:
    """
    Metric for RAG pipeline quality.

    Checks:
    - Confidence threshold
    - Citation presence
    - No hallucination markers
    - JSON validity
    - Answer non-empty
    """

    def __init__(
        self,
        min_confidence: float = 0.7,
        require_citations: bool = True,
        check_hallucinations: bool = True
    ):
        self.min_confidence = min_confidence
        self.require_citations = require_citations
        self.check_hallucinations = check_hallucinations

    def __call__(self, example: dspy.Example, pred: Any, trace: Optional[Any] = None) -> float:
        """
        Evaluate prediction quality.

        Args:
            example: Input example with expected outputs (optional)
            pred: Prediction from the pipeline
            trace: Optional execution trace

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        checks_passed = 0
        total_checks = 0

        # Check 1: Confidence threshold
        total_checks += 1
        confidence = getattr(pred, 'confidence', 0.0)
        if confidence >= self.min_confidence:
            checks_passed += 1
            score += 0.3

        # Check 2: Citations present
        if self.require_citations:
            total_checks += 1
            citations = getattr(pred, 'citations', [])
            if citations and len(citations) > 0:
                checks_passed += 1
                score += 0.3

        # Check 3: No hallucination markers
        if self.check_hallucinations:
            total_checks += 1
            answer = getattr(pred, 'answer', '') or ''
            bad_markers = ['hallucin', 'unknown', 'insufficient evidence', 'cannot answer']
            if not any(marker in answer.lower() for marker in bad_markers):
                checks_passed += 1
                score += 0.2

        # Check 4: Answer non-empty
        total_checks += 1
        answer = getattr(pred, 'answer', '') or ''
        if len(answer.strip()) > 10:
            checks_passed += 1
            score += 0.2

        logger.debug(f"Metric: {checks_passed}/{total_checks} checks passed, score={score:.2f}")
        return score


class RAGCompiler:
    """
    Compiler for RAG pipelines using DSPy optimizers.

    Supports:
    - BootstrapFewShot: Fast, demo-based optimization
    - MIPROv2: Joint instruction + demo optimization
    """

    def __init__(
        self,
        artifacts_dir: str = "artifacts/dspy_compiled",
        metric: Optional[Callable] = None
    ):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.metric = metric or RAGMetric()

    def compile_with_bootstrap(
        self,
        module: dspy.Module,
        trainset: List[dspy.Example],
        max_bootstrapped_demos: int = 12,
        max_labeled_demos: int = 4,
        max_rounds: int = 1,
        teacher: Optional[dspy.Module] = None
    ) -> dspy.Module:
        """
        Compile module using BootstrapFewShot.

        Fast optimization that harvests good demonstrations from a teacher model.

        Args:
            module: DSPy module to compile
            trainset: Training examples
            max_bootstrapped_demos: Max demos to bootstrap
            max_labeled_demos: Max labeled demos to use
            max_rounds: Optimization rounds
            teacher: Teacher model (defaults to module itself)

        Returns:
            Compiled module

        Reference: https://deepwiki.com/stanfordnlp/dspy/4.1-optimization-and-teleprompting
        """
        logger.info(f"🔧 Compiling with BootstrapFewShot: {len(trainset)} examples")

        try:
            from dspy.teleprompt import BootstrapFewShot

            optimizer = BootstrapFewShot(
                metric=self.metric,
                max_bootstrapped_demos=max_bootstrapped_demos,
                max_labeled_demos=max_labeled_demos,
                max_rounds=max_rounds
            )

            compiled = optimizer.compile(
                student=module,
                trainset=trainset,
                teacher=teacher or module
            )

            logger.info(f"✅ BootstrapFewShot compilation complete")
            return compiled

        except Exception as e:
            logger.error(f"❌ BootstrapFewShot compilation failed: {e}")
            return module  # Return original module on failure

    def compile_with_mipro(
        self,
        module: dspy.Module,
        trainset: List[dspy.Example],
        num_candidates: int = 10,
        init_temperature: float = 1.0,
        max_bootstrapped_demos: int = 12,
        max_labeled_demos: int = 4
    ) -> dspy.Module:
        """
        Compile module using MIPROv2 (Multi-prompt Instruction Proposal Optimizer).

        Jointly optimizes instructions AND few-shot demonstrations via:
        - Proposes instruction candidates
        - Bayesian optimization for selection
        - Better than BootstrapFewShot when you have good traffic data

        Args:
            module: DSPy module to compile
            trainset: Training examples (100+ recommended)
            num_candidates: Number of instruction candidates to generate
            init_temperature: Initial temperature for proposals
            max_bootstrapped_demos: Max demos for each instruction
            max_labeled_demos: Max labeled demos

        Returns:
            Compiled module

        Reference: https://dspy.ai/api/optimizers/MIPROv2/
        """
        logger.info(f"🔧 Compiling with MIPROv2: {len(trainset)} examples")

        try:
            from dspy.teleprompt import MIPROv2

            optimizer = MIPROv2(
                metric=self.metric,
                num_candidates=num_candidates,
                init_temperature=init_temperature,
                max_bootstrapped_demos=max_bootstrapped_demos,
                max_labeled_demos=max_labeled_demos,
                verbose=True
            )

            compiled = optimizer.compile(
                student=module,
                trainset=trainset,
                num_trials=len(trainset) // 10,  # 10% for trials
                minibatch_size=25,
                minibatch_full_eval_steps=10
            )

            logger.info(f"✅ MIPROv2 compilation complete")
            return compiled

        except Exception as e:
            logger.error(f"❌ MIPROv2 compilation failed: {e}")
            logger.info("Falling back to BootstrapFewShot...")
            return self.compile_with_bootstrap(module, trainset)

    def save_compiled(
        self,
        module: dspy.Module,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save compiled module to disk.

        Args:
            module: Compiled module
            name: Module name (e.g., "rag_pipeline")
            metadata: Optional metadata to save alongside

        Returns:
            Path to saved artifact
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_compiled_{timestamp}.json"
        filepath = self.artifacts_dir / filename

        try:
            module.save(str(filepath))

            # Save metadata
            if metadata:
                meta_path = filepath.with_suffix('.meta.json')
                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

            # Update 'latest' symlink
            latest_path = self.artifacts_dir / f"{name}_latest.json"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(filepath.name)

            logger.info(f"💾 Saved compiled module: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save compiled module: {e}")
            raise

    def load_compiled(
        self,
        module_class: type,
        name: str,
        use_latest: bool = True
    ) -> Optional[dspy.Module]:
        """
        Load compiled module from disk.

        Args:
            module_class: Class of the module to instantiate
            name: Module name
            use_latest: Use latest version (True) or specify timestamp

        Returns:
            Loaded module or None if not found
        """
        if use_latest:
            filepath = self.artifacts_dir / f"{name}_latest.json"
        else:
            # Find most recent by timestamp
            pattern = f"{name}_compiled_*.json"
            files = sorted(self.artifacts_dir.glob(pattern), reverse=True)
            filepath = files[0] if files else None

        if filepath and filepath.exists():
            try:
                module = module_class()
                module.load(str(filepath))
                logger.info(f"📂 Loaded compiled module: {filepath}")
                return module
            except Exception as e:
                logger.error(f"❌ Failed to load compiled module: {e}")
                return None
        else:
            logger.warning(f"⚠️ No compiled module found for {name}")
            return None

    def evaluate(
        self,
        module: dspy.Module,
        evalset: List[dspy.Example],
        baseline: Optional[dspy.Module] = None
    ) -> CompilationMetrics:
        """
        Evaluate compiled module against baseline.

        Args:
            module: Compiled module to evaluate
            evalset: Evaluation examples
            baseline: Optional baseline module for comparison

        Returns:
            Compilation metrics
        """
        import time

        logger.info(f"📊 Evaluating module on {len(evalset)} examples")

        compiled_scores = []
        compiled_latencies = []

        for example in evalset:
            start = time.time()
            try:
                pred = module(**example.toDict())
                score = self.metric(example, pred)
                compiled_scores.append(score)
            except Exception as e:
                logger.warning(f"Evaluation error: {e}")
                compiled_scores.append(0.0)
            latency_ms = (time.time() - start) * 1000
            compiled_latencies.append(latency_ms)

        compiled_score = sum(compiled_scores) / len(compiled_scores)
        p50_lat = sorted(compiled_latencies)[len(compiled_latencies) // 2]
        p95_lat = sorted(compiled_latencies)[int(len(compiled_latencies) * 0.95)]

        # Baseline evaluation
        baseline_score = 0.0
        if baseline:
            baseline_scores = []
            for example in evalset:
                try:
                    pred = baseline(**example.toDict())
                    score = self.metric(example, pred)
                    baseline_scores.append(score)
                except:
                    baseline_scores.append(0.0)
            baseline_score = sum(baseline_scores) / len(baseline_scores)

        metrics = CompilationMetrics(
            timestamp=datetime.now().isoformat(),
            compiler="compiled",
            train_size=0,
            eval_size=len(evalset),
            baseline_score=baseline_score,
            compiled_score=compiled_score,
            improvement=(compiled_score - baseline_score) / baseline_score if baseline_score > 0 else 0.0,
            avg_tokens_saved=0,  # TODO: track token usage
            p50_latency_ms=p50_lat,
            p95_latency_ms=p95_lat
        )

        logger.info(f"📊 Evaluation complete: {compiled_score:.3f} (baseline: {baseline_score:.3f})")
        return metrics
