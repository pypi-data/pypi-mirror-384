"""
Adaptive Token Budgeting for DSPy RAG
Stage-aware token allocation to prevent context overflow
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenAllocation:
    """Token allocation for a stage"""
    stage: str
    input_tokens: int
    allocated_tokens: int
    max_tokens: int
    utilization: float


class AdaptiveTokenBudget:
    """
    Adaptive token budgeting for multi-stage pipelines.

    Allocates tokens based on:
    - Stage complexity (weights)
    - Input size (dynamic adjustment)
    - Model context window (hard cap)
    """

    def __init__(
        self,
        model_context_window: int = 8192,
        safety_margin: float = 0.12
    ):
        """
        Args:
            model_context_window: Maximum tokens for the model
            safety_margin: Reserve percentage for overhead (default: 12%)
        """
        self.context_window = model_context_window
        self.safety_margin = safety_margin
        self.available_tokens = int(model_context_window * (1 - safety_margin))

        # Stage weights (should sum to 1.0)
        self.stage_weights = {
            'rewrite': 0.10,      # Query rewriting is short
            'retrieve': 0.15,     # Retrieval queries are brief
            'curate': 0.35,       # Curation needs moderate space
            'structure': 0.40,    # Structuring needs most space
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens from text.

        Rough approximation: ~4 characters per token for English,
        ~2-3 for Arabic (more compact). Average to ~3.5 chars/token.
        """
        return len(text) // 3.5

    def allocate(
        self,
        stage: str,
        input_text: str,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> TokenAllocation:
        """
        Allocate tokens for a stage.

        Args:
            stage: Stage name (e.g., 'rewrite', 'curate')
            input_text: Input text for the stage
            messages: Optional message list for more accurate estimation

        Returns:
            TokenAllocation with recommended max_tokens
        """
        # Estimate input tokens
        if messages:
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            input_tokens = int(total_chars / 3.5)
        else:
            input_tokens = int(self.estimate_tokens(input_text))

        # Get stage weight
        weight = self.stage_weights.get(stage, 0.33)  # Default: 1/3

        # Calculate base allocation
        stage_budget = int(self.available_tokens * weight)

        # Adjust for input size (leave room for output)
        available_for_output = max(512, stage_budget - input_tokens)

        # Cap at stage maximum based on complexity
        stage_max = self._get_stage_max(stage)
        allocated = min(available_for_output, stage_max)

        utilization = input_tokens / self.context_window

        allocation = TokenAllocation(
            stage=stage,
            input_tokens=input_tokens,
            allocated_tokens=allocated,
            max_tokens=stage_max,
            utilization=utilization
        )

        logger.debug(
            f"Token allocation [{stage}]: "
            f"input={input_tokens}, allocated={allocated}, "
            f"util={utilization:.1%}"
        )

        # Warn if approaching context limit
        if utilization > 0.7:
            logger.warning(
                f"⚠️ High token utilization ({utilization:.1%}) for stage '{stage}'. "
                f"Consider truncation or pipeline splitting."
            )

        return allocation

    def _get_stage_max(self, stage: str) -> int:
        """Get maximum tokens for a stage based on complexity"""
        stage_maximums = {
            'rewrite': 256,       # Rewrites are concise
            'retrieve': 512,      # Retrieval packaging is brief
            'curate': 2048,       # Curation needs moderate space
            'structure': 3500,    # Structuring needs most space
        }
        return stage_maximums.get(stage, 2048)

    def check_overflow_risk(self, stages: List[str], inputs: Dict[str, str]) -> bool:
        """
        Check if pipeline risks context overflow.

        Args:
            stages: List of stage names
            inputs: Dict of stage -> input text

        Returns:
            True if overflow risk detected
        """
        total_input = sum(
            int(self.estimate_tokens(inputs.get(stage, "")))
            for stage in stages
        )

        # Estimate output tokens (conservative: 80% of allocation)
        total_output = sum(
            int(self._get_stage_max(stage) * 0.8)
            for stage in stages
        )

        total = total_input + total_output
        risk = total > self.context_window

        if risk:
            logger.warning(
                f"⚠️ Context overflow risk: {total}/{self.context_window} tokens "
                f"({total/self.context_window:.1%})"
            )

        return risk

    def suggest_split(self, stages: List[str]) -> tuple[List[str], List[str]]:
        """
        Suggest how to split pipeline to avoid overflow.

        Returns:
            (first_batch, second_batch) of stages
        """
        # Split at natural boundary (e.g., after retrieval)
        split_after = ['retrieve', 'curate']

        for split_stage in split_after:
            if split_stage in stages:
                idx = stages.index(split_stage) + 1
                return stages[:idx], stages[idx:]

        # Fallback: split in half
        mid = len(stages) // 2
        return stages[:mid], stages[mid:]

    def adaptive_k(self, stage: str, current_k: int, confidence: float) -> int:
        """
        Adaptively adjust retrieval k based on confidence.

        Args:
            stage: Stage name
            current_k: Current k value
            confidence: Confidence score from previous stage

        Returns:
            Adjusted k value
        """
        if stage != 'retrieve':
            return current_k

        # Escalate k if low confidence
        if confidence < 0.5:
            new_k = min(current_k * 2, 48)  # Double up to 48
            logger.info(f"📈 Escalating k: {current_k} → {new_k} (low confidence)")
            return new_k
        elif confidence < 0.7:
            new_k = min(int(current_k * 1.5), 32)  # 1.5x up to 32
            logger.info(f"📈 Increasing k: {current_k} → {new_k} (medium confidence)")
            return new_k

        return current_k


# Global budget instance for Falcon (8192 context window)
falcon_budget = AdaptiveTokenBudget(model_context_window=8192, safety_margin=0.12)

# Global budget instance for OpenAI (128k context window for GPT-4)
openai_budget = AdaptiveTokenBudget(model_context_window=128000, safety_margin=0.10)


def get_budget(provider: str = 'falcon') -> AdaptiveTokenBudget:
    """Get token budget for provider (defaults to Falcon)"""
    if provider == 'openai':
        return openai_budget
    return falcon_budget
