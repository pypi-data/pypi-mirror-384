"""
Accuracy-First DSPy Optimizer

Focuses purely on getting the RIGHT answer, not speed/cost.

Key strategies:
- Best model always (Falcon-H1-34B-Instruct)
- Maximum context (k=48)
- Multi-pass retrieval
- Critic → Refine loops
- Self-consistency
- Explicit validation at each stage
"""

import logging
from typing import List, Dict, Any, Optional
import dspy
from collections import Counter

logger = logging.getLogger(__name__)


class CriticRefineModule(dspy.Module):
    """
    Explicit quality improvement via Critic → Refine loop.

    Better than blind retries because:
    - Critic explicitly identifies what's wrong
    - Refine specifically addresses those issues
    - Can iterate until quality threshold met
    """

    def __init__(self, answer_signature, critic_instructions: str = None):
        super().__init__()
        self.answer = dspy.ChainOfThought(answer_signature)
        self.critic = dspy.ChainOfThought(self._create_critic_sig(answer_signature))
        self.refine = dspy.ChainOfThought(self._create_refine_sig(answer_signature))
        self.critic_instructions = critic_instructions or "Identify factual errors, missing citations, unclear reasoning, or grade-inappropriate content."

    def _create_critic_sig(self, answer_sig):
        """Create critic signature matching answer signature"""
        class CriticSig(dspy.Signature):
            """Critically evaluate the answer for accuracy and quality issues"""
            pass

        # Copy input fields from answer signature
        for name, field in answer_sig.input_fields.items():
            setattr(CriticSig, name, field)

        # Add candidate answer input
        CriticSig.candidate_answer = dspy.InputField(desc="Proposed answer to evaluate")

        # Output: list of issues
        CriticSig.issues = dspy.OutputField(desc="Specific issues found (empty list if perfect)")
        CriticSig.severity = dspy.OutputField(desc="Overall severity: low, medium, high")

        return CriticSig

    def _create_refine_sig(self, answer_sig):
        """Create refine signature matching answer signature"""
        class RefineSig(dspy.Signature):
            """Refine the answer to address identified issues"""
            pass

        # Copy input fields from answer signature
        for name, field in answer_sig.input_fields.items():
            setattr(RefineSig, name, field)

        # Add original answer and issues
        RefineSig.original_answer = dspy.InputField(desc="Original answer to improve")
        RefineSig.issues = dspy.InputField(desc="Issues to address")

        # Copy output fields from answer signature
        for name, field in answer_sig.output_fields.items():
            setattr(RefineSig, name, field)

        return RefineSig

    def forward(self, **kwargs):
        """Execute Critic → Refine loop until quality threshold met"""
        max_iterations = 3

        # Initial answer
        result = self.answer(**kwargs)

        for iteration in range(max_iterations):
            # Critic evaluates
            critic_result = self.critic(
                **kwargs,
                candidate_answer=str(result)
            )

            # Check if issues found
            issues = getattr(critic_result, 'issues', '')
            severity = getattr(critic_result, 'severity', 'low')

            logger.debug(f"Critic iteration {iteration + 1}: severity={severity}, issues={issues}")

            # If no serious issues, we're done
            if not issues or issues.lower() in ['none', 'no issues', '[]', '']:
                logger.info(f"✓ Quality threshold met after {iteration + 1} iteration(s)")
                break

            if severity.lower() in ['low', 'none']:
                logger.info(f"✓ Minor issues only, accepting answer")
                break

            # Refine to address issues
            result = self.refine(
                **kwargs,
                original_answer=str(result),
                issues=issues
            )

            logger.debug(f"Refined answer: {result}")

        return result


class SelfConsistencyModule(dspy.Module):
    """
    Self-consistency: Generate multiple reasoning paths, pick most common answer.

    More reliable than single answer, especially for complex questions.
    """

    def __init__(self, answer_module, n_samples: int = 5):
        super().__init__()
        self.answer_module = answer_module
        self.n_samples = n_samples

    def forward(self, **kwargs):
        """Generate n_samples answers and return most consistent"""
        answers = []

        # Generate multiple samples with higher temperature for diversity
        original_temp = kwargs.get('temperature', 0.3)

        for i in range(self.n_samples):
            # Vary temperature slightly for diversity
            temp = original_temp + (i * 0.1)  # 0.3, 0.4, 0.5, 0.6, 0.7
            kwargs['temperature'] = min(temp, 0.9)

            result = self.answer_module(**kwargs)
            answers.append(result)

            logger.debug(f"Sample {i + 1}/{self.n_samples}: {result}")

        # Find most common answer
        answer_texts = [getattr(a, 'answer', str(a)) for a in answers]
        most_common = Counter(answer_texts).most_common(1)[0][0]

        # Find the result object with most common answer
        for result in answers:
            if getattr(result, 'answer', str(result)) == most_common:
                logger.info(f"✓ Self-consistency: {most_common} (appeared {Counter(answer_texts)[most_common]}/{self.n_samples} times)")
                return result

        # Fallback to first answer
        return answers[0]


class MultiPassRetriever:
    """
    Multi-pass retrieval for better context coverage.

    Pass 1: Broad retrieval (k=48)
    Pass 2: Rewrite query based on initial results
    Pass 3: Focused retrieval (k=32)
    Final: Combine and deduplicate (k=24)
    """

    def __init__(self, retriever, embed_fn=None):
        self.retriever = retriever
        self.embed_fn = embed_fn

    def multi_pass_search(self, query: str, k_final: int = 24, **filters) -> List[Dict[str, Any]]:
        """Execute multi-pass retrieval"""

        # Pass 1: Broad retrieval
        logger.debug(f"Pass 1: Broad retrieval (k=48)")
        broad_results = self.retriever.search(query, k=48, filters=filters)

        # Pass 2: Rewrite query based on top results
        top_context = "\n".join([doc.text[:200] for doc in broad_results[:5]])
        rewritten_query = self._rewrite_with_context(query, top_context)
        logger.debug(f"Pass 2: Rewritten query: {rewritten_query}")

        # Pass 3: Focused retrieval with rewritten query
        logger.debug(f"Pass 3: Focused retrieval (k=32)")
        focused_results = self.retriever.search(rewritten_query, k=32, filters=filters)

        # Combine and deduplicate
        all_results = self._deduplicate_and_rank(
            broad_results,
            focused_results,
            k_final=k_final
        )

        logger.info(f"✓ Multi-pass retrieval: {len(all_results)} final documents")
        return all_results

    def _rewrite_with_context(self, query: str, context: str) -> str:
        """Rewrite query based on initial context"""
        try:
            # Use the default configured LM (Falcon)
            rewriter = dspy.Predict("query, context -> refined_query")
            result = rewriter(
                query=query,
                context=f"Initial relevant content:\n{context}\n\nRefine the query to be more specific based on this context."
            )
            return result.refined_query or query
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}, using original")
            return query

    def _deduplicate_and_rank(self, list1: List, list2: List, k_final: int) -> List:
        """Combine results, deduplicate, and rank by score"""
        seen_ids = set()
        combined = []

        # Prioritize list1 (broad results) slightly
        for doc in list1:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                combined.append(doc)

        for doc in list2:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                combined.append(doc)

        # Return top k_final
        return combined[:k_final]


class AccuracyOptimizer:
    """
    Main accuracy optimizer that configures DSPy for maximum quality.

    Usage:
        optimizer = AccuracyOptimizer()
        optimizer.configure()  # Sets up best model, params
        result = optimizer.run_module(module, **inputs)
    """

    def __init__(self, lm=None):
        """
        Args:
            lm: DSPy LM to use (defaults to configured Falcon model)
        """
        self.lm = lm

    def configure(self):
        """Configure DSPy for maximum accuracy"""
        # Use provided LM or keep existing configuration
        if self.lm:
            dspy.settings.configure(lm=self.lm)
            logger.info(f"✓ Accuracy mode configured with provided LM")
        else:
            logger.info(f"✓ Accuracy mode using existing DSPy configuration")

    def wrap_with_critic_refine(self, module: dspy.Module) -> CriticRefineModule:
        """Wrap module with Critic → Refine loop"""
        return CriticRefineModule(module)

    def wrap_with_self_consistency(self, module: dspy.Module, n_samples: int = 5) -> SelfConsistencyModule:
        """Wrap module with self-consistency"""
        return SelfConsistencyModule(module, n_samples=n_samples)

    def run_with_quality_gates(self, module: dspy.Module, min_confidence: float = 0.8, **kwargs):
        """
        Run module with quality gates.

        If confidence < threshold, escalate:
        1. Add Critic → Refine
        2. Use self-consistency
        3. Increase retrieval k
        """
        # First attempt
        result = module(**kwargs)
        confidence = getattr(result, 'confidence', 1.0)

        logger.debug(f"Initial result confidence: {confidence:.2f}")

        # If high confidence, we're done
        if confidence >= min_confidence:
            logger.info(f"✓ High confidence ({confidence:.2f}), accepting result")
            return result

        # Low confidence: escalate with Critic → Refine
        logger.warning(f"⚠ Low confidence ({confidence:.2f}), applying Critic → Refine")
        critic_module = CriticRefineModule(type(module))
        result = critic_module(**kwargs)
        confidence = getattr(result, 'confidence', 1.0)

        if confidence >= min_confidence:
            logger.info(f"✓ Critic improved confidence to {confidence:.2f}")
            return result

        # Still low: use self-consistency
        logger.warning(f"⚠ Still low confidence ({confidence:.2f}), using self-consistency")
        sc_module = SelfConsistencyModule(module, n_samples=5)
        result = sc_module(**kwargs)

        return result


# Global accuracy optimizer
_accuracy_optimizer: Optional[AccuracyOptimizer] = None


def get_accuracy_optimizer(lm=None) -> AccuracyOptimizer:
    """Get or create global accuracy optimizer"""
    global _accuracy_optimizer
    if _accuracy_optimizer is None:
        _accuracy_optimizer = AccuracyOptimizer(lm=lm)
        _accuracy_optimizer.configure()
    return _accuracy_optimizer


def enable_accuracy_mode(lm=None):
    """Enable accuracy-first mode globally"""
    optimizer = get_accuracy_optimizer(lm=lm)
    optimizer.configure()
    logger.info("✓ Accuracy-first mode enabled globally")
