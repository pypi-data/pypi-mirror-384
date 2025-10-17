#!/usr/bin/env python3
"""
Parameter generator submodule for creating diverse question parameters.
"""

import logging
import random
import hashlib
from typing import Dict, Any, Tuple, List, Set
from dataclasses import dataclass
from src.utils.timing_utils import time_operation, timed_function
from src.llms import _llm_gpt5

logger = logging.getLogger(__name__)


@dataclass
class GeneratedParameters:
    """Container for generated parameters."""
    values: Dict[str, Any]
    generation_method: str
    uniqueness_hash: str


class ParameterGenerator:
    """
    Generates diverse parameters for question patterns.
    Ensures no duplicate parameter sets are generated.
    """

    def __init__(self):
        self.used_parameter_hashes: Set[str] = set()
        self.parameter_history: List[Dict[str, Any]] = []
        self.max_history = 100

        logger.info("ParameterGenerator initialized")

    @timed_function("ParameterGenerator.generate_unique_parameters")
    def generate_unique_parameters(
        self,
        pattern: Dict[str, Any],
        difficulty: str = "medium",
        force_unique: bool = True
    ) -> GeneratedParameters:
        """
        Generate unique parameters for a pattern.

        Args:
            pattern: Pattern dictionary with parameter_ranges
            difficulty: Difficulty level affecting parameter complexity
            force_unique: If True, ensures parameters are not duplicated

        Returns:
            GeneratedParameters object with unique values
        """
        param_ranges = pattern.get('parameter_ranges', {})

        if not param_ranges:
            logger.warning("Pattern has no parameter ranges, using defaults")
            param_ranges = self._get_default_ranges(pattern, difficulty)

        max_attempts = 5  # Reduced for speed - no Gemini fallback
        attempt = 0

        with time_operation("Parameter generation with uniqueness"):
            while attempt < max_attempts:
                attempt += 1

                # Use only fast local generation - disable slow Gemini calls
                params = self._generate_by_difficulty(
                    param_ranges, difficulty, pattern, attempt)

                # Create hash for uniqueness check
                param_hash = self._hash_parameters(params)

                # Check uniqueness if required
                if not force_unique or param_hash not in self.used_parameter_hashes:
                    self.used_parameter_hashes.add(param_hash)
                    self.parameter_history.append(params)

                    # Trim history if too large
                    if len(self.parameter_history) > self.max_history:
                        self.parameter_history = self.parameter_history[-self.max_history:]

                    logger.info(
                        f"Generated unique parameters on attempt {attempt}: {params}")

                    return GeneratedParameters(
                        values=params,
                        generation_method=f"difficulty_{difficulty}_attempt_{attempt}",
                        uniqueness_hash=param_hash
                    )

                logger.debug(
                    f"Parameters not unique, retrying (attempt {attempt})")

            # Fallback: generate with random variation
            logger.warning(
                "Max attempts reached, generating with forced variation")
            params = self._generate_with_variation(param_ranges, difficulty)
            param_hash = self._hash_parameters(params)

            return GeneratedParameters(
                values=params,
                generation_method="forced_variation_fallback",
                uniqueness_hash=param_hash
            )

    def _generate_by_difficulty(
        self,
        param_ranges: Dict[str, Tuple],
        difficulty: str,
        pattern: Dict[str, Any],
        attempt: int = 1
    ) -> Dict[str, Any]:
        """Generate parameters based on difficulty level."""
        params = {}

        for param_name, range_spec in param_ranges.items():
            if isinstance(range_spec, tuple) and len(range_spec) == 2:
                min_val, max_val = range_spec

                # Add variation based on attempt number to ensure uniqueness
                variation_seed = attempt * 17 + hash(param_name) % 100
                random.seed(variation_seed)

                # Adjust range based on difficulty
                if difficulty == "easy":
                    # Use simpler values with attempt-based variation
                    adjusted_min = max(min_val, 1)
                    adjusted_max = min(max_val, min_val +
                                       (max_val - min_val) // 3)
                    # Add attempt variation
                    range_expand = (attempt - 1) * 2
                    adjusted_max = min(max_val, adjusted_max + range_expand)
                    value = random.randint(adjusted_min, adjusted_max)
                    # Prefer round numbers for easy, but vary with attempts
                    if value > 10 and (attempt % 3 != 0):
                        value = (value // 5) * 5

                elif difficulty == "medium":
                    # Use middle range with attempt-based shifting
                    mid_point = (min_val + max_val) // 2
                    range_size = (max_val - min_val) // 2
                    # Shift range based on attempt
                    shift = (attempt - 1) * 3
                    adjusted_min = max(min_val, mid_point -
                                       range_size // 2 - shift)
                    adjusted_max = min(max_val, mid_point +
                                       range_size // 2 + shift)
                    value = random.randint(adjusted_min, adjusted_max)

                elif difficulty in ["hard", "expert"]:
                    # Use full range with attempt-based variation
                    if (attempt % 3 == 0):  # Every 3rd attempt use lower range
                        adjusted_min = min_val
                        adjusted_max = min_val + (max_val - min_val) // 2
                    else:
                        adjusted_min = min_val + (max_val - min_val) // 3
                        adjusted_max = max_val

                    value = random.randint(adjusted_min, adjusted_max)

                    # Add complexity for expert with attempt variation
                    if difficulty == "expert" and (attempt % 4 == 0):
                        value = self._get_interesting_value(
                            adjusted_min, adjusted_max)
                else:
                    # Default with attempt variation
                    offset = (attempt - 1) * 5
                    adjusted_min = max(min_val, min_val + offset)
                    adjusted_max = min(max_val, max_val - offset)
                    if adjusted_min >= adjusted_max:
                        adjusted_min, adjusted_max = min_val, max_val
                    value = random.randint(adjusted_min, adjusted_max)

                # Reset random seed
                random.seed()

                params[param_name] = value

            elif isinstance(range_spec, list):
                # Choice from list
                params[param_name] = random.choice(range_spec)
            else:
                # Direct value
                params[param_name] = range_spec

        # Special handling for specific pattern types
        operation_type = pattern.get('operation_type', '')
        if 'quadratic' in operation_type.lower():
            params = self._adjust_quadratic_parameters(params, difficulty)
        elif 'linear' in operation_type.lower():
            params = self._adjust_linear_parameters(params, difficulty)

        return params

    def _generate_with_variation(
        self,
        param_ranges: Dict[str, Tuple],
        difficulty: str
    ) -> Dict[str, Any]:
        """Generate parameters with forced variation from history."""
        params = {}

        for param_name, range_spec in param_ranges.items():
            if isinstance(range_spec, tuple) and len(range_spec) == 2:
                min_val, max_val = range_spec

                # Get historical values for this parameter
                historical_values = [
                    p.get(param_name, 0)
                    for p in self.parameter_history[-10:]
                    if param_name in p
                ]

                # Generate value avoiding recent ones
                attempts = 0
                while attempts < 20:
                    value = random.randint(min_val, max_val)
                    if value not in historical_values or attempts > 15:
                        params[param_name] = value
                        break
                    attempts += 1
            else:
                params[param_name] = range_spec

        return params

    def _generate_with_gemini(
        self,
        param_ranges: Dict[str, Tuple],
        difficulty: str,
        pattern: Dict[str, Any],
        attempt: int = 1
    ) -> Dict[str, Any]:
        """Generate parameters using Gemini Flash for grade-specific complexity."""

        # Extract context
        operation_type = pattern.get('operation_type', 'general')
        formula = pattern.get('mathematical_formula', '')
        subject = pattern.get('subject', 'mathematics')
        grade = pattern.get('grade', 8)

        # Build simplified prompt for speed
        param_specs = []
        for param_name, range_spec in param_ranges.items():
            if isinstance(range_spec, tuple) and len(range_spec) == 2:
                min_val, max_val = range_spec
                param_specs.append(f"{param_name}: {min_val}-{max_val}")

        prompt = f"""Generate Grade {grade} {difficulty} math parameters. Attempt #{attempt}.

Parameters: {', '.join(param_specs)}

Requirements:
- Grade {grade}: {"simple numbers" if grade <= 6 else "moderate numbers" if grade <= 9 else "complex numbers"}  
- {difficulty}: {"easy calculations" if difficulty == "easy" else "moderate calculations" if difficulty == "medium" else "challenging calculations"}
- Unique from previous attempts
- Use EXACT parameter names with underscore: param_0, param_1, etc.

Return JSON only: {{"param_0": value1, "param_1": value2}}"""

        try:
            response = _llm_gpt5.invoke(prompt)
            response_text = response.content.strip()

            # Clean response
            if response_text.startswith('```json'):
                response_text = response_text.replace(
                    '```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            # Parse JSON
            import json
            params = json.loads(response_text)

            # Validate parameters are within ranges and exist in template
            valid_params = {}
            for param_name, range_spec in param_ranges.items():
                if isinstance(range_spec, tuple) and len(range_spec) == 2:
                    min_val, max_val = range_spec
                    if param_name in params:
                        value = params[param_name]
                        if isinstance(value, (int, float)) and min_val <= value <= max_val:
                            valid_params[param_name] = value
                        else:
                            # Replace with fallback value
                            valid_params[param_name] = random.randint(
                                min_val, max_val)
                            logger.warning(
                                f"Parameter {param_name} out of range, using fallback")
                    else:
                        # Generate missing parameter
                        valid_params[param_name] = random.randint(
                            min_val, max_val)
                        logger.warning(
                            f"Parameter {param_name} missing from Gemini, generated fallback")

            # Remove any parameters not in template
            for param_name in list(params.keys()):
                if param_name not in param_ranges:
                    logger.warning(
                        f"Removing unexpected parameter {param_name} from Gemini")

            params = valid_params

            logger.info(f"Gemini generated parameters: {params}")
            return params

        except Exception as e:
            logger.error(f"Gemini parameter generation failed: {e}")
            # Fallback to original method
            return self._generate_by_difficulty(param_ranges, difficulty, pattern, attempt)

    def _adjust_quadratic_parameters(
        self,
        params: Dict[str, Any],
        difficulty: str
    ) -> Dict[str, Any]:
        """Adjust parameters specifically for quadratic equations."""

        # Ensure we have a, b, c parameters
        if 'a' in params and 'b' in params and 'c' in params:
            a, b, c = params['a'], params['b'], params['c']

            # Calculate discriminant
            discriminant = b**2 - 4*a*c

            if difficulty == "easy":
                # Ensure integer roots (perfect discriminant)
                # Adjust c to make discriminant a perfect square
                if discriminant < 0 or not self._is_perfect_square(discriminant):
                    # Find nearest perfect square discriminant
                    target_disc = self._nearest_perfect_square(
                        abs(discriminant))
                    params['c'] = (b**2 - target_disc) // (4 *
                                                           a) if a != 0 else c

            elif difficulty == "expert":
                # Sometimes create complex roots
                if random.random() < 0.2:  # 20% chance
                    # Make discriminant negative
                    params['c'] = (b**2 + random.randint(1, 10)
                                   ) // (4*a) if a != 0 else c

        return params

    def _adjust_linear_parameters(
        self,
        params: Dict[str, Any],
        difficulty: str
    ) -> Dict[str, Any]:
        """Adjust parameters specifically for linear equations."""

        if difficulty == "easy":
            # Ensure simple integer solutions
            if 'a' in params and 'b' in params:
                # Make b divisible by a for integer solution
                if params['a'] != 0 and params['b'] % params['a'] != 0:
                    params['b'] = params['a'] * random.randint(1, 10)

        return params

    def _get_interesting_value(self, min_val: int, max_val: int) -> int:
        """Get mathematically interesting values (primes, squares, etc)."""
        interesting_values = []

        # Prime numbers
        primes = [p for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
                  if min_val <= p <= max_val]
        interesting_values.extend(primes)

        # Perfect squares
        squares = [i**2 for i in range(1, 20) if min_val <= i**2 <= max_val]
        interesting_values.extend(squares)

        # Fibonacci numbers
        fibs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        interesting_values.extend([f for f in fibs if min_val <= f <= max_val])

        if interesting_values:
            return random.choice(interesting_values)

        return random.randint(min_val, max_val)

    def _is_perfect_square(self, n: int) -> bool:
        """Check if a number is a perfect square."""
        if n < 0:
            return False
        root = int(n ** 0.5)
        return root * root == n

    def _nearest_perfect_square(self, n: int) -> int:
        """Find the nearest perfect square to n."""
        root = int(n ** 0.5)
        lower = root * root
        upper = (root + 1) * (root + 1)

        if abs(n - lower) <= abs(n - upper):
            return lower
        return upper

    def _get_default_ranges(
        self,
        pattern: Dict[str, Any],
        difficulty: str
    ) -> Dict[str, Tuple[int, int]]:
        """Get default parameter ranges based on pattern type."""
        operation_type = pattern.get('operation_type', 'general')

        if 'quadratic' in operation_type.lower():
            if difficulty == "easy":
                return {
                    'a': (1, 2),
                    'b': (-10, 10),
                    'c': (-10, 10)
                }
            elif difficulty == "medium":
                return {
                    'a': (1, 5),
                    'b': (-20, 20),
                    'c': (-20, 20)
                }
            else:  # hard/expert
                return {
                    'a': (1, 10),
                    'b': (-50, 50),
                    'c': (-50, 50)
                }
        else:
            # General default
            if difficulty == "easy":
                return {'param_0': (1, 10), 'param_1': (1, 10)}
            elif difficulty == "medium":
                return {'param_0': (1, 50), 'param_1': (1, 50)}
            else:
                return {'param_0': (1, 100), 'param_1': (1, 100)}

    def _hash_parameters(self, params: Dict[str, Any]) -> str:
        """Create a hash of parameters for uniqueness checking."""
        # Sort keys for consistent hashing
        sorted_items = sorted(params.items())
        param_str = '|'.join(f"{k}:{v}" for k, v in sorted_items)
        return hashlib.md5(param_str.encode()).hexdigest()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parameter generation."""
        stats = {
            'total_generated': len(self.used_parameter_hashes),
            'unique_hashes': len(self.used_parameter_hashes),
            'history_size': len(self.parameter_history)
        }

        # Parameter value distributions
        if self.parameter_history:
            param_stats = {}
            all_params = set()
            for p in self.parameter_history:
                all_params.update(p.keys())

            for param_name in all_params:
                values = [p.get(param_name)
                          for p in self.parameter_history if param_name in p]
                if values:
                    param_stats[param_name] = {
                        'min': min(values),
                        'max': max(values),
                        'unique_count': len(set(values))
                    }

            stats['parameter_distributions'] = param_stats

        return stats

    def reset(self):
        """Reset the generator state."""
        self.used_parameter_hashes.clear()
        self.parameter_history.clear()
        logger.info("ParameterGenerator state reset")
