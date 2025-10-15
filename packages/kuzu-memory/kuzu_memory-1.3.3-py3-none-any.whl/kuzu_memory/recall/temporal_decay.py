"""
Enhanced Temporal Decay System for KuzuMemory

Provides sophisticated temporal decay algorithms that gradually reduce memory
relevance over time while preserving important information.
"""

import logging
import math
from datetime import datetime
from enum import Enum
from typing import Any

from ..core.models import Memory, MemoryType

logger = logging.getLogger(__name__)


class DecayFunction(Enum):
    """Different temporal decay function types."""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    SIGMOID = "sigmoid"
    POWER_LAW = "power_law"
    STEP = "step"


class TemporalDecayEngine:
    """
    Advanced temporal decay engine with multiple decay functions and
    sophisticated configuration options.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize temporal decay engine.

        Args:
            config: Configuration for decay parameters
        """
        self.config = config or {}

        # Default decay configuration
        self.decay_config = {
            "base_weight": self.config.get(
                "recency_weight", 0.20
            ),  # Increased from 0.10
            "decay_function": DecayFunction(
                self.config.get("decay_function", "exponential")
            ),
            "enable_adaptive_decay": self.config.get("enable_adaptive_decay", True),
            "boost_recent_threshold_hours": self.config.get(
                "boost_recent_threshold_hours", 24
            ),
            "boost_recent_multiplier": self.config.get("boost_recent_multiplier", 1.5),
            "minimum_decay_score": self.config.get("minimum_decay_score", 0.01),
            "maximum_decay_score": self.config.get("maximum_decay_score", 1.0),
        }

        # Memory type-specific decay parameters
        self.type_decay_params = {
            MemoryType.SEMANTIC: {
                "half_life_days": 365,  # Very slow decay (facts, identity)
                "decay_function": DecayFunction.LINEAR,
                "minimum_score": 0.8,  # Never goes below 80%
                "boost_multiplier": 1.0,  # No recency boost needed
            },
            MemoryType.PREFERENCE: {
                "half_life_days": 180,  # Slow decay
                "decay_function": DecayFunction.EXPONENTIAL,
                "minimum_score": 0.6,  # Never goes below 60%
                "boost_multiplier": 1.2,  # Slight recency boost
            },
            MemoryType.PROCEDURAL: {
                "half_life_days": 90,  # Medium decay (patterns, solutions)
                "decay_function": DecayFunction.SIGMOID,
                "minimum_score": 0.3,  # Can decay to 30%
                "boost_multiplier": 1.3,  # Recent procedures important
            },
            MemoryType.WORKING: {
                "half_life_days": 1,  # Very fast decay (current tasks)
                "decay_function": DecayFunction.EXPONENTIAL,
                "minimum_score": 0.01,  # Can decay almost completely
                "boost_multiplier": 2.0,  # Recent status very important
            },
            MemoryType.EPISODIC: {
                "half_life_days": 30,  # Medium decay (experiences)
                "decay_function": DecayFunction.POWER_LAW,
                "minimum_score": 0.05,  # Can decay significantly
                "boost_multiplier": 1.5,  # Recent events important
            },
            MemoryType.SENSORY: {
                "half_life_days": 0.25,  # Very fast decay (6 hours)
                "decay_function": DecayFunction.EXPONENTIAL,
                "minimum_score": 0.01,  # Can decay almost completely
                "boost_multiplier": 2.5,  # Very recent sensory data important
            },
        }

        # Override with custom configuration
        custom_params = self.config.get("type_decay_params", {})
        for memory_type_str, params in custom_params.items():
            try:
                memory_type = MemoryType(memory_type_str)
                if memory_type in self.type_decay_params:
                    self.type_decay_params[memory_type].update(params)
            except ValueError:
                logger.warning(f"Unknown memory type in config: {memory_type_str}")

    def calculate_temporal_score(
        self, memory: Memory, current_time: datetime | None = None
    ) -> float:
        """
        Calculate temporal decay score for a memory.

        Args:
            memory: Memory to calculate score for
            current_time: Current time (defaults to now)

        Returns:
            Temporal decay score between 0.0 and 1.0
        """
        if current_time is None:
            current_time = datetime.now()

        # Get memory type parameters
        params = self.type_decay_params.get(
            memory.memory_type, self.type_decay_params[MemoryType.PROCEDURAL]
        )

        # Calculate age (handle None created_at gracefully)
        if memory.created_at is None:
            logger.warning(
                f"Memory {memory.id} has None created_at, using current time"
            )
            memory.created_at = current_time
        age = current_time - memory.created_at
        age_days = age.total_seconds() / (24 * 3600)
        age_hours = age.total_seconds() / 3600

        # Calculate base decay score
        decay_score = self._calculate_decay_score(age_days, params)

        # Apply recent boost if enabled
        if (
            self.decay_config["enable_adaptive_decay"]
            and age_hours < self.decay_config["boost_recent_threshold_hours"]
        ):
            boost_multiplier = params.get("boost_multiplier", 1.0)
            recent_boost = (
                self.decay_config["boost_recent_multiplier"] * boost_multiplier
            )

            # Gradual boost that decreases as memory gets older within the threshold
            boost_factor = 1 - (
                age_hours / self.decay_config["boost_recent_threshold_hours"]
            )
            decay_score *= 1 + (recent_boost - 1) * boost_factor

        # Apply bounds
        min_score = params.get(
            "minimum_score", self.decay_config["minimum_decay_score"]
        )
        max_score = params.get(
            "maximum_score", self.decay_config["maximum_decay_score"]
        )

        return max(min_score, min(max_score, decay_score))

    def _calculate_decay_score(self, age_days: float, params: dict[str, Any]) -> float:
        """Calculate decay score using the specified decay function."""

        half_life = params.get("half_life_days", 30)
        decay_function = params.get("decay_function", DecayFunction.EXPONENTIAL)

        if decay_function == DecayFunction.EXPONENTIAL:
            return self._exponential_decay(age_days, half_life)
        elif decay_function == DecayFunction.LINEAR:
            return self._linear_decay(age_days, half_life)
        elif decay_function == DecayFunction.LOGARITHMIC:
            return self._logarithmic_decay(age_days, half_life)
        elif decay_function == DecayFunction.SIGMOID:
            return self._sigmoid_decay(age_days, half_life)
        elif decay_function == DecayFunction.POWER_LAW:
            return self._power_law_decay(age_days, half_life)
        elif decay_function == DecayFunction.STEP:
            return self._step_decay(age_days, half_life)
        else:
            return self._exponential_decay(age_days, half_life)

    def _exponential_decay(self, age_days: float, half_life: float) -> float:
        """Exponential decay: score = exp(-age / half_life)"""
        return math.exp(-age_days / half_life)

    def _linear_decay(self, age_days: float, half_life: float) -> float:
        """Linear decay: score = max(0, 1 - age / (2 * half_life))"""
        return max(0.0, 1.0 - age_days / (2 * half_life))

    def _logarithmic_decay(self, age_days: float, half_life: float) -> float:
        """Logarithmic decay: score = 1 / (1 + log(1 + age / half_life))"""
        return 1.0 / (1.0 + math.log(1.0 + age_days / half_life))

    def _sigmoid_decay(self, age_days: float, half_life: float) -> float:
        """Sigmoid decay: score = 1 / (1 + exp((age - half_life) / (half_life / 4)))"""
        steepness = half_life / 4
        return 1.0 / (1.0 + math.exp((age_days - half_life) / steepness))

    def _power_law_decay(self, age_days: float, half_life: float) -> float:
        """Power law decay: score = (half_life / (half_life + age))^2"""
        return (half_life / (half_life + age_days)) ** 2

    def _step_decay(self, age_days: float, half_life: float) -> float:
        """Step decay: discrete steps at intervals"""
        if age_days < half_life / 4:
            return 1.0
        elif age_days < half_life / 2:
            return 0.8
        elif age_days < half_life:
            return 0.6
        elif age_days < half_life * 2:
            return 0.4
        elif age_days < half_life * 4:
            return 0.2
        else:
            return 0.1

    def get_decay_explanation(
        self, memory: Memory, current_time: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get detailed explanation of temporal decay calculation.

        Args:
            memory: Memory to explain
            current_time: Current time (defaults to now)

        Returns:
            Dictionary with decay calculation details
        """
        if current_time is None:
            current_time = datetime.now()

        params = self.type_decay_params.get(
            memory.memory_type, self.type_decay_params[MemoryType.PROCEDURAL]
        )
        age = current_time - memory.created_at
        age_days = age.total_seconds() / (24 * 3600)
        age_hours = age.total_seconds() / 3600

        base_score = self._calculate_decay_score(age_days, params)
        final_score = self.calculate_temporal_score(memory, current_time)

        # Check if recent boost was applied
        recent_boost_applied = (
            self.decay_config["enable_adaptive_decay"]
            and age_hours < self.decay_config["boost_recent_threshold_hours"]
        )

        return {
            "memory_id": memory.id,
            "memory_type": memory.memory_type.value,
            "age_days": round(age_days, 2),
            "age_hours": round(age_hours, 2),
            "decay_function": params.get(
                "decay_function", DecayFunction.EXPONENTIAL
            ).value,
            "half_life_days": params.get("half_life_days", 30),
            "base_decay_score": round(base_score, 4),
            "final_temporal_score": round(final_score, 4),
            "recent_boost_applied": recent_boost_applied,
            "minimum_score": params.get("minimum_score", 0.01),
            "boost_multiplier": params.get("boost_multiplier", 1.0),
            "parameters_used": params,
        }

    def configure_memory_type_decay(self, memory_type: MemoryType, **kwargs):
        """
        Configure decay parameters for a specific memory type.

        Args:
            memory_type: Memory type to configure
            **kwargs: Decay parameters to update
        """
        if memory_type not in self.type_decay_params:
            self.type_decay_params[memory_type] = {}

        self.type_decay_params[memory_type].update(kwargs)
        logger.info(f"Updated decay parameters for {memory_type.value}: {kwargs}")

    def get_effective_weight(
        self, memory: Memory, current_time: datetime | None = None
    ) -> float:
        """
        Get the effective temporal weight for a memory in ranking.

        This combines the base temporal weight with the decay score.

        Args:
            memory: Memory to calculate weight for
            current_time: Current time (defaults to now)

        Returns:
            Effective temporal weight for ranking
        """
        temporal_score = self.calculate_temporal_score(memory, current_time)
        base_weight = self.decay_config["base_weight"]

        return base_weight * temporal_score
