"""
Contextual UCB Bandit for Model/Config Selection

Routes traffic between baseline, compiled, and alternative LLMs based on:
- Confidence scores
- Latency
- Cost
- Context (grade, subject, difficulty)
"""

import time
import math
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ArmStats:
    """Statistics for a bandit arm (model/config)"""
    pulls: int = 0
    total_reward: float = 0.0
    avg_reward: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_cents: float = 0.0
    total_latency_ms: float = 0.0
    total_cost_cents: float = 0.0

    def update(self, reward: float, latency_ms: float, cost_cents: float):
        """Update arm statistics with new observation"""
        self.pulls += 1
        self.total_reward += reward
        self.avg_reward = self.total_reward / self.pulls

        self.total_latency_ms += latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.pulls

        self.total_cost_cents += cost_cents
        self.avg_cost_cents = self.total_cost_cents / self.pulls


@dataclass
class ContextualBandit:
    """
    Contextual UCB bandit for model selection.

    Maintains per-context statistics and uses Upper Confidence Bound
    to balance exploration vs exploitation.
    """

    arms: list[str] = field(default_factory=lambda: ["baseline", "compiled", "gpt4o_mini"])
    exploration_factor: float = 2.0

    # Context -> Arm -> Stats
    context_stats: Dict[str, Dict[str, ArmStats]] = field(default_factory=lambda: defaultdict(dict))

    def _get_context_key(self, grade: Optional[int], subject: Optional[str],
                         difficulty: Optional[str]) -> str:
        """Generate context key for bucketing"""
        return f"{grade or 'any'}_{subject or 'any'}_{difficulty or 'any'}"

    def _ucb_score(self, arm: str, context_key: str, total_pulls: int) -> float:
        """Calculate UCB score for an arm in a context"""
        if context_key not in self.context_stats or arm not in self.context_stats[context_key]:
            # Unobserved arm gets high exploration bonus
            return float('inf')

        stats = self.context_stats[context_key][arm]
        if stats.pulls == 0:
            return float('inf')

        # UCB formula: avg_reward + c * sqrt(ln(total_pulls) / arm_pulls)
        exploration_bonus = self.exploration_factor * math.sqrt(
            math.log(max(1, total_pulls)) / stats.pulls
        )

        return stats.avg_reward + exploration_bonus

    def select_arm(self, grade: Optional[int] = None, subject: Optional[str] = None,
                   difficulty: Optional[str] = None) -> str:
        """Select best arm using UCB for given context"""
        context_key = self._get_context_key(grade, subject, difficulty)

        # Get total pulls for this context
        total_pulls = sum(
            stats.pulls
            for stats in self.context_stats.get(context_key, {}).values()
        )

        # Calculate UCB scores for all arms
        scores = {
            arm: self._ucb_score(arm, context_key, total_pulls)
            for arm in self.arms
        }

        # Select arm with highest UCB score
        selected = max(scores.items(), key=lambda x: x[1])[0]

        logger.debug(f"Bandit selection for {context_key}: {selected} "
                    f"(scores: {[(k, f'{v:.3f}') for k, v in scores.items()]})")

        return selected

    def compute_reward(self, confidence: float, latency_ms: float, cost_cents: float) -> float:
        """
        Compute reward from execution metrics.

        Reward = confidence - latency_penalty - cost_penalty
        """
        latency_penalty = 0.001 * latency_ms  # 1ms = -0.001 reward
        cost_penalty = 0.01 * cost_cents      # 1 cent = -0.01 reward

        return max(0.0, confidence) - latency_penalty - cost_penalty

    def update(self, arm: str, confidence: float, latency_ms: float,
               cost_cents: float, grade: Optional[int] = None,
               subject: Optional[str] = None, difficulty: Optional[str] = None):
        """Update arm statistics after execution"""
        context_key = self._get_context_key(grade, subject, difficulty)

        # Initialize context and arm if needed
        if context_key not in self.context_stats:
            self.context_stats[context_key] = {}
        if arm not in self.context_stats[context_key]:
            self.context_stats[context_key][arm] = ArmStats()

        # Compute reward and update
        reward = self.compute_reward(confidence, latency_ms, cost_cents)
        self.context_stats[context_key][arm].update(reward, latency_ms, cost_cents)

        logger.debug(f"Bandit update: arm={arm}, context={context_key}, "
                    f"reward={reward:.3f}, conf={confidence:.3f}, "
                    f"lat={latency_ms}ms, cost={cost_cents:.3f}¢")

    def get_stats(self, context: Optional[str] = None) -> Dict[str, Any]:
        """Get bandit statistics, optionally for specific context"""
        if context:
            return {
                arm: {
                    'pulls': stats.pulls,
                    'avg_reward': stats.avg_reward,
                    'avg_latency_ms': stats.avg_latency_ms,
                    'avg_cost_cents': stats.avg_cost_cents
                }
                for arm, stats in self.context_stats.get(context, {}).items()
            }

        # Aggregate across all contexts
        aggregate = defaultdict(lambda: {'pulls': 0, 'total_reward': 0.0,
                                         'total_latency': 0.0, 'total_cost': 0.0})

        for ctx_stats in self.context_stats.values():
            for arm, stats in ctx_stats.items():
                aggregate[arm]['pulls'] += stats.pulls
                aggregate[arm]['total_reward'] += stats.total_reward
                aggregate[arm]['total_latency'] += stats.total_latency_ms
                aggregate[arm]['total_cost'] += stats.total_cost_cents

        return {
            arm: {
                'pulls': data['pulls'],
                'avg_reward': data['total_reward'] / data['pulls'] if data['pulls'] > 0 else 0,
                'avg_latency_ms': data['total_latency'] / data['pulls'] if data['pulls'] > 0 else 0,
                'avg_cost_cents': data['total_cost'] / data['pulls'] if data['pulls'] > 0 else 0
            }
            for arm, data in aggregate.items()
        }

    def save(self, filepath: str):
        """Save bandit state to file"""
        state = {
            'arms': self.arms,
            'exploration_factor': self.exploration_factor,
            'context_stats': {
                ctx: {
                    arm: {
                        'pulls': stats.pulls,
                        'total_reward': stats.total_reward,
                        'avg_reward': stats.avg_reward,
                        'avg_latency_ms': stats.avg_latency_ms,
                        'avg_cost_cents': stats.avg_cost_cents,
                        'total_latency_ms': stats.total_latency_ms,
                        'total_cost_cents': stats.total_cost_cents
                    }
                    for arm, stats in arm_stats.items()
                }
                for ctx, arm_stats in self.context_stats.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Saved bandit state to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'ContextualBandit':
        """Load bandit state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)

        bandit = cls(
            arms=state['arms'],
            exploration_factor=state['exploration_factor']
        )

        # Restore context stats
        for ctx, arm_stats in state['context_stats'].items():
            bandit.context_stats[ctx] = {}
            for arm, stats_dict in arm_stats.items():
                bandit.context_stats[ctx][arm] = ArmStats(**stats_dict)

        logger.info(f"Loaded bandit state from {filepath}")
        return bandit


# Global bandit instance
_global_bandit: Optional[ContextualBandit] = None


def get_bandit() -> ContextualBandit:
    """Get or create global bandit instance"""
    global _global_bandit
    if _global_bandit is None:
        _global_bandit = ContextualBandit()
    return _global_bandit


def select_model(grade: Optional[int] = None, subject: Optional[str] = None,
                 difficulty: Optional[str] = None) -> str:
    """Select best model using bandit"""
    return get_bandit().select_arm(grade, subject, difficulty)


def update_bandit(arm: str, confidence: float, latency_ms: float, cost_cents: float,
                  grade: Optional[int] = None, subject: Optional[str] = None,
                  difficulty: Optional[str] = None):
    """Update bandit with execution results"""
    get_bandit().update(arm, confidence, latency_ms, cost_cents, grade, subject, difficulty)
