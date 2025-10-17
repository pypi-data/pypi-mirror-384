#!/usr/bin/env python3
"""
Pattern selector submodule for ensuring diverse question generation.
"""

import logging
import random
import hashlib
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from src.utils.timing_utils import time_operation, timed_function

logger = logging.getLogger(__name__)


@dataclass
class PatternSelection:
    """Result of pattern selection."""
    pattern: Dict[str, Any]
    selection_reason: str
    diversity_score: float


class PatternSelector:
    """
    Ensures diverse pattern selection for question generation.
    Prevents repetition and tracks pattern usage.
    """

    def __init__(self):
        self.used_patterns: Set[str] = set()
        self.pattern_usage_count: Dict[str, int] = {}
        self.last_patterns: List[str] = []
        self.max_history = 10

        logger.info("PatternSelector initialized")

    @timed_function("PatternSelector.select_diverse_patterns")
    def select_diverse_patterns(
        self,
        available_patterns: List[Dict[str, Any]],
        quantity: int,
        subject: str,
        grade: int,
        difficulty: str
    ) -> List[PatternSelection]:
        """
        Select diverse patterns ensuring no repetition.

        Returns list of PatternSelection objects with diversity guarantees.
        """
        logger.info(
            f"Selecting {quantity} diverse patterns from {len(available_patterns)} available")

        with time_operation(f"Pattern filtering for {subject} grade {grade}"):
            # Filter patterns by criteria
            filtered_patterns = self._filter_patterns(
                available_patterns, subject, grade, difficulty
            )

        if not filtered_patterns:
            logger.warning("No patterns match criteria, using all available")
            filtered_patterns = available_patterns

        with time_operation("Pattern diversity selection"):
            selected = []
            attempts = 0
            max_attempts = quantity * 10

            while len(selected) < quantity and attempts < max_attempts:
                attempts += 1

                # Select pattern with diversity scoring
                pattern = self._select_with_diversity(
                    filtered_patterns, selected)

                if pattern:
                    # Create unique hash for this pattern instance
                    pattern_hash = self._generate_pattern_hash(pattern)

                    # Check if too similar to recently selected
                    if not self._is_too_similar(pattern, selected):
                        selection = PatternSelection(
                            pattern=pattern,
                            selection_reason=f"Diversity score: {self._calculate_diversity_score(pattern, selected):.2f}",
                            diversity_score=self._calculate_diversity_score(
                                pattern, selected)
                        )
                        selected.append(selection)
                        self.used_patterns.add(pattern_hash)

                        # Track usage
                        pattern_type = pattern.get('operation_type', 'unknown')
                        self.pattern_usage_count[pattern_type] = self.pattern_usage_count.get(
                            pattern_type, 0) + 1

                        logger.info(
                            f"Selected pattern {len(selected)}/{quantity}: {pattern_type} (attempt {attempts})")
                    else:
                        logger.debug(
                            f"Pattern too similar, retrying (attempt {attempts})")

            if len(selected) < quantity:
                logger.warning(
                    f"Could only select {len(selected)}/{quantity} diverse patterns")
                # Fill remaining with random patterns
                while len(selected) < quantity and filtered_patterns:
                    pattern = random.choice(filtered_patterns)
                    selected.append(PatternSelection(
                        pattern=pattern,
                        selection_reason="Random fallback",
                        diversity_score=0.0
                    ))

        self._log_selection_stats(selected)
        return selected

    def _filter_patterns(
        self,
        patterns: List[Dict[str, Any]],
        subject: str,
        grade: int,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Filter patterns by subject, grade, and difficulty."""
        filtered = []

        for pattern in patterns:
            # More permissive subject match - allow general math patterns
            subject_match = True
            if pattern.get('subject', ''):
                pattern_subject = pattern.get('subject', '').lower()
                if (subject.lower() not in pattern_subject and
                    pattern_subject not in subject.lower() and
                        pattern_subject not in ['math', 'mathematics', 'general']):
                    subject_match = False

            # More permissive grade range - allow ±3 grades
            grade_match = True
            pattern_grade = pattern.get('grade')
            if pattern_grade and abs(pattern_grade - grade) > 3:
                grade_match = False

            # More permissive difficulty - only filter extreme mismatches
            difficulty_match = True
            pattern_difficulty = pattern.get('difficulty', 'medium')
            if difficulty == 'expert' and pattern_difficulty == 'easy':
                difficulty_match = False
            elif difficulty == 'easy' and pattern_difficulty == 'expert':
                difficulty_match = False

            # Accept pattern if it meets relaxed criteria
            if subject_match and grade_match and difficulty_match:
                filtered.append(pattern)

        logger.info(
            f"Filtered {len(patterns)} patterns to {len(filtered)} matching criteria")
        return filtered

    def _select_with_diversity(
        self,
        patterns: List[Dict[str, Any]],
        already_selected: List[PatternSelection]
    ) -> Dict[str, Any]:
        """Select a pattern maximizing diversity from already selected ones."""
        if not already_selected:
            # First selection - prefer less used pattern types
            return self._select_least_used_type(patterns)

        # Score all patterns by diversity
        scored_patterns = []
        for pattern in patterns:
            score = self._calculate_diversity_score(pattern, already_selected)
            scored_patterns.append((score, pattern))

        # Sort by diversity score (higher is better)
        scored_patterns.sort(key=lambda x: x[0], reverse=True)

        # Select from top 20% with some randomness
        top_count = max(1, len(scored_patterns) // 5)
        top_patterns = scored_patterns[:top_count]

        if top_patterns:
            return random.choice(top_patterns)[1]

        return random.choice(patterns) if patterns else None

    def _select_least_used_type(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select pattern from least used operation type."""
        type_counts = {}
        for pattern in patterns:
            op_type = pattern.get('operation_type', 'unknown')
            if op_type not in type_counts:
                type_counts[op_type] = []
            type_counts[op_type].append(pattern)

        # Sort by usage count
        sorted_types = sorted(
            type_counts.items(),
            key=lambda x: self.pattern_usage_count.get(x[0], 0)
        )

        if sorted_types:
            # Select from least used type
            least_used_patterns = sorted_types[0][1]
            return random.choice(least_used_patterns)

        return random.choice(patterns) if patterns else None

    def _calculate_diversity_score(
        self,
        pattern: Dict[str, Any],
        selected: List[PatternSelection]
    ) -> float:
        """Calculate diversity score for a pattern relative to selected ones."""
        if not selected:
            return 1.0

        score = 0.0

        # Factor 1: Different operation type (40% weight)
        op_type = pattern.get('operation_type', 'unknown')
        selected_types = [s.pattern.get(
            'operation_type', 'unknown') for s in selected]
        if op_type not in selected_types:
            score += 0.4
        elif selected_types.count(op_type) == 1:
            score += 0.2

        # Factor 2: Different difficulty (20% weight)
        difficulty = pattern.get('difficulty', 'medium')
        selected_difficulties = [s.pattern.get(
            'difficulty', 'medium') for s in selected]
        if difficulty not in selected_difficulties:
            score += 0.2

        # Factor 3: Different parameter ranges (20% weight)
        param_ranges = pattern.get('parameter_ranges', {})
        for sel in selected:
            sel_ranges = sel.pattern.get('parameter_ranges', {})
            if param_ranges != sel_ranges:
                score += 0.2 / len(selected)

        # Factor 4: Different mathematical formula structure (20% weight)
        formula = pattern.get('mathematical_formula', '')
        selected_formulas = [s.pattern.get(
            'mathematical_formula', '') for s in selected]
        if formula and formula not in selected_formulas:
            score += 0.2

        return min(1.0, score)  # Cap at 1.0

    def _is_too_similar(
        self,
        pattern: Dict[str, Any],
        selected: List[PatternSelection]
    ) -> bool:
        """Check if pattern is too similar to already selected ones."""
        if not selected:
            return False

        # Check for exact template match
        template = pattern.get('template', '')
        for sel in selected:
            if sel.pattern.get('template', '') == template:
                logger.debug(f"Rejecting pattern - exact template match")
                return True

        # Check for very similar mathematical formula
        formula = pattern.get('mathematical_formula', '')
        if formula:
            for sel in selected:
                sel_formula = sel.pattern.get('mathematical_formula', '')
                if sel_formula and self._formula_similarity(formula, sel_formula) > 0.9:
                    logger.debug(f"Rejecting pattern - formula too similar")
                    return True

        return False

    def _formula_similarity(self, formula1: str, formula2: str) -> float:
        """Calculate similarity between two mathematical formulas."""
        if formula1 == formula2:
            return 1.0

        # Simple character-based similarity
        common = set(formula1) & set(formula2)
        total = set(formula1) | set(formula2)

        if not total:
            return 0.0

        return len(common) / len(total)

    def _generate_pattern_hash(self, pattern: Dict[str, Any]) -> str:
        """Generate unique hash for a pattern."""
        key_parts = [
            pattern.get('template', ''),
            pattern.get('mathematical_formula', ''),
            str(pattern.get('parameter_ranges', {})),
            pattern.get('operation_type', '')
        ]
        key = '|'.join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()

    def _log_selection_stats(self, selected: List[PatternSelection]):
        """Log statistics about pattern selection."""
        logger.info("=" * 50)
        logger.info("PATTERN SELECTION STATISTICS")
        logger.info("=" * 50)

        # Count by operation type
        type_counts = {}
        for sel in selected:
            op_type = sel.pattern.get('operation_type', 'unknown')
            type_counts[op_type] = type_counts.get(op_type, 0) + 1

        logger.info(f"Selected {len(selected)} patterns:")
        for op_type, count in type_counts.items():
            logger.info(f"  - {op_type}: {count}")

        # Average diversity score
        avg_diversity = sum(s.diversity_score for s in selected) / \
            len(selected) if selected else 0
        logger.info(f"Average diversity score: {avg_diversity:.2f}")

        logger.info("=" * 50)

    def reset(self):
        """Reset the selector state."""
        self.used_patterns.clear()
        self.pattern_usage_count.clear()
        self.last_patterns.clear()
        logger.info("PatternSelector state reset")
