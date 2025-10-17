"""
DSPy Production Improvements - Modern Stack

Production-grade enhancements for DSPy RAG pipelines:
- Hybrid retrieval (RRF + MMR)
- Automatic compilation (BootstrapFewShot / MIPROv2)
- Smart caching (TTL-based LRU)
- Adaptive token budgeting
- Bandit routing (contextual UCB)
- Assertions & auto-healing
"""

from .hybrid_retrieval import (
    reciprocal_rank_fusion,
    maximal_marginal_relevance,
    hybrid_search,
    ScoredDoc,
    normalize_vectors
)

from .compiler import (
    RAGCompiler,
    RAGMetric,
    CompilationMetrics
)

from .caching import (
    TTLCache,
    CacheManager,
    cache_manager,
    cache_rewrite,
    cache_search,
    cache_llm
)

from .token_budget import (
    AdaptiveTokenBudget,
    TokenAllocation,
    falcon_budget,
    openai_budget,
    get_budget
)

from .bandit import (
    ContextualBandit,
    ArmStats,
    get_bandit,
    select_model,
    update_bandit
)

from .assertions import (
    HealingConfig,
    AssertionValidator,
    with_auto_healing,
    validate_output,
    assert_citations,
    assert_confidence,
    assert_answer_present,
    assert_no_hallucination_markers,
    assert_grade_appropriate,
    assert_json_valid
)

from .accuracy_optimizer import (
    AccuracyOptimizer,
    CriticRefineModule,
    SelfConsistencyModule,
    MultiPassRetriever,
    get_accuracy_optimizer,
    enable_accuracy_mode
)

__all__ = [
    # Hybrid Retrieval
    'reciprocal_rank_fusion',
    'maximal_marginal_relevance',
    'hybrid_search',
    'ScoredDoc',
    'normalize_vectors',

    # Compilation
    'RAGCompiler',
    'RAGMetric',
    'CompilationMetrics',

    # Caching
    'TTLCache',
    'CacheManager',
    'cache_manager',
    'cache_rewrite',
    'cache_search',
    'cache_llm',

    # Token Budgeting
    'AdaptiveTokenBudget',
    'TokenAllocation',
    'falcon_budget',
    'openai_budget',
    'get_budget',

    # Bandit Routing
    'ContextualBandit',
    'ArmStats',
    'get_bandit',
    'select_model',
    'update_bandit',

    # Assertions & Auto-Healing
    'HealingConfig',
    'AssertionValidator',
    'with_auto_healing',
    'validate_output',
    'assert_citations',
    'assert_confidence',
    'assert_answer_present',
    'assert_no_hallucination_markers',
    'assert_grade_appropriate',
    'assert_json_valid',

    # Accuracy Optimizer
    'AccuracyOptimizer',
    'CriticRefineModule',
    'SelfConsistencyModule',
    'MultiPassRetriever',
    'get_accuracy_optimizer',
    'enable_accuracy_mode',
]

__version__ = '2.1.0'
