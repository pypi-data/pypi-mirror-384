#!/usr/bin/env python3
"""
Module 1: Simple RAG + PostgreSQL Retrieval
Subject/grade agnostic. Simple retrieval with structured output — THAT’S ALL.

RAG is powered by DSPyMongoRAG (Mongo via LangChain's MongoDBAtlasVectorSearch).
GPT fallback uses solve_with_llm + parse_json only.
"""

import os
import re
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- SQL functionality (stubbed) ---
# import psycopg2  # Stubbed - using PostgreSQL function from dev_upload_util instead

# LLM entrypoints
from src.llms import format_messages_for_api,  solve_with_llm, dspy_lm
from src.utils.json_repair import parse_json, to_dict

# Your vector store helper
from src.utils.vector_store import get_vector_store_textbooks

# Your DSPy RAG engine (the one-class file you shared)
from src.dspy_rag import DSPyMongoRAG
import dspy
from pydantic import BaseModel, Field
from typing import Dict

# PostgreSQL retrieval function
from src.utils.dev_upload_util import retrieve_patterns_and_samples_psql

from src.llms import produce_structured_response

# Optional: fetch raw docs for fields
try:
    from bson import ObjectId
except Exception:
    ObjectId = None

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logger = logging.getLogger(__name__)


# DSPy Signature for skill instruction parsing
class SkillInstructionParser(dspy.Signature):
    """Parse structured skill title into educational components for targeted content retrieval."""
    skill_title = dspy.InputField(desc="Skill title")
    unit_name = dspy.InputField(desc="Unit name")
    lesson_title = dspy.InputField(desc="Lesson title")
    standard_description = dspy.InputField(desc="Educational standard description")
    sys_instructions = dspy.InputField(desc="Specific instructions")
    grade = dspy.InputField(desc="Target grade level")
    subject = dspy.InputField(desc="Subject area")
    language = dspy.InputField(desc="Target language")

    parsed_components = dspy.OutputField(desc="JSON object with: focus_topic, learning_objectives, key_concepts, search_terms, priority_elements")


class EducationalContentRetriever(dspy.Signature):
    """Generate targeted educational content retrieval query based on parsed skill components."""
    skill_title = dspy.InputField(desc="Main skill title")
    unit_name = dspy.InputField(desc="Unit name")
    lesson_title = dspy.InputField(desc="Lesson title")
    standard_description = dspy.InputField(desc="Educational standard")
    sys_instructions = dspy.InputField(desc="Specific instructions")
    focus_topic = dspy.InputField(desc="Focused topic from parsing")
    grade = dspy.InputField(desc="Target grade level")
    subject = dspy.InputField(desc="Subject area")
    language = dspy.InputField(desc="Target language")

    optimized_query = dspy.OutputField(desc="Educational content query optimized for vector search")


# --------------------------
# Output model for Module 1
# --------------------------
@dataclass
class RetrievedSample:
    """Structured output for retrieved samples (agnostic)."""
    question_text: str
    subject_area: str
    grade: int
    topic: str
    difficulty: str
    language: str
    answer: Optional[str] = None
    explanation: Optional[str] = None
    source: str = "Vector Store"


# ---------------------------------
# Module 1 RAG + (optional) SQL mix
# ---------------------------------
class Module1RAGRetriever:
    """
    Module 1: Subject/grade agnostic retrieval.
    - Primary: DSPy/Mongo RAG via DSPyMongoRAG
    - Optional: SQL (left intact)
    - Fallback: solve_with_llm + parse_json
    """

    def __init__(self, enable_compilation: bool = False, accuracy_mode: bool = False):  # Default to DSPy mode
        """
        Initialize Module 1 RAG Retriever

        Args:
            enable_compilation: If True, attempt to load compiled RAG pipeline
            accuracy_mode: If True, optimize for accuracy (GPT-4o, k=48, etc.)
        """
        self.POSTGRES_URI = os.getenv("POSTGRES_URI")
        self.accuracy_mode = accuracy_mode

        # Use your existing vector store factory
        self.vector_store = get_vector_store_textbooks()

        # PRODUCTION: Balanced for speed/cost
        self.rag = DSPyMongoRAG(
            vector_store=self.vector_store,
            enable_hybrid=True,
            mmr_lambda=0.6,        # 60% relevance, 40% diversity
            provider='dspy'        # Use DSPy for consistency
        )
        logger.info("✓ Module 1 initialized in PRODUCTION MODE (DSPy, k=12, MMR λ=0.6)")

        # Try to load compiled version if requested
        if enable_compilation:
            try:
                from src.dspy_improvements import RAGCompiler
                compiler = RAGCompiler(artifacts_dir="artifacts/dspy_compiled")
                compiled_rag = compiler.load_compiled(DSPyMongoRAG, "rag_pipeline")
                if compiled_rag:
                    self.rag = compiled_rag
                    logger.info("✅ Loaded compiled RAG pipeline from artifacts/dspy_compiled/rag_pipeline/")
                else:
                    logger.info("⚠️ No compiled pipeline found, using baseline RAG")
            except Exception as e:
                logger.warning(f"Could not load compiled pipeline: {e}, using baseline RAG")

        # DSPy components for skill-aware retrieval
        self.skill_parser = dspy.ChainOfThought(SkillInstructionParser)
        self.content_retriever = dspy.ChainOfThought(EducationalContentRetriever)

        # Set DSPy LLM
        dspy.settings.configure(lm=dspy_lm)


    # --------------------------------------
    # Public: get N retrieved samples (agn.)
    # --------------------------------------
    def retrieve_samples(
        self,
        grade: int,
        subject: str,
        limit: int = 5,
        skill_title: Optional[str] = None,
        language: str = "arabic",
        provider: str = "openai",
        exclude_question_texts: Optional[set] = None,
    ) -> List[RetrievedSample]:
        """
        Return up to `limit` retrieved samples using multi-strategy retrieval.

        Accuracy mode: k=48, multi-pass retrieval, best model
        Production mode: k=12, single-pass, balanced model

        Args:
            exclude_question_texts: Set of question texts to exclude (from Module 0 DB pull)
        """
        # Adjust k based on accuracy mode
        k = 48 if self.accuracy_mode else 12
        logger.debug(f"Retrieval k={k} ({'ACCURACY' if self.accuracy_mode else 'PRODUCTION'} mode)")

        rag_samples: List[RetrievedSample] = []
        psql_samples: List[RetrievedSample] = []

        skill_components = self._parse_skill_title_with_dspy(
            skill_title or "",
            grade,
            subject,
            language
        )

        query = self._generate_skill_aware_query(
            skill_components,
            grade,
            subject,
            language
        )

        # Derive skill focus and terms for alignment from parsed components and inputs
        skill_focus = (
            (skill_components.get('focus_topic') or "").strip()
            or (skill_components.get('skill_title') or "").strip()
            or (skill_title or "").strip()
            or subject
        )
        skill_terms: List[str] = []
        for key in ['skill_title', 'focus_topic', 'instructions']:
            val = (skill_components.get(key) or "").strip()
            if val:
                skill_terms.extend(re.split(r"[^\w\u0600-\u06FF]+", val))
        for key in ['key_concepts', 'search_terms']:
            arr = skill_components.get(key) or []
            if isinstance(arr, list):
                for v in arr:
                    if isinstance(v, str) and v.strip():
                        skill_terms.extend(re.split(r"[^\w\u0600-\u06FF]+", v.strip()))
        skill_terms = [t.lower() for t in skill_terms if t and len(t) >= 3]
        seen_t = set()
        dedup_terms: List[str] = []
        for t in skill_terms:
            if t not in seen_t:
                dedup_terms.append(t)
                seen_t.add(t)
        skill_terms = dedup_terms[:12]

        # RAG retrieval only (PostgreSQL disabled for performance)
        try:
            rag_samples = self._rag_retrieve(
                limit=limit,
                subject=subject,
                grade=grade,
                language=language,
                query=query,
                skill_terms=skill_terms,
                skill_focus=skill_focus,
            )

        except Exception as e:
            logger.warning(f"Module 1 RAG retrieval failed: {e}")
            rag_samples = []

        # Direct PostgreSQL retrieval (no need for ThreadPool with single task)
        try:
            psql_result = retrieve_patterns_and_samples_psql(
                grade=grade,
                subject=subject,
                quantity=limit,
                skill_title=skill_title,
                language=language
            )
            psql_samples = psql_result.get("samples", []) if psql_result else []
        except Exception as e:
            logger.warning(f"Module 1 PostgreSQL retrieval failed: {e}")
            psql_samples = []

        # Combine RAG and PostgreSQL results, removing duplicates
        combined = self._merge_sample_sources(rag_samples, psql_samples, limit, exclude_question_texts)
        combined = self.evaluate_and_update_samples(combined, grade, subject, query, skill_focus, provider, limit)
        # convert combined dicts to list of RetrievedSample objects
        combined = [RetrievedSample(**sample) for sample in combined]

        # Additional deduplication against Module 0 DB questions
        if exclude_question_texts:
            original_count = len(combined)
            combined = [s for s in combined if s.question_text.lower().strip() not in exclude_question_texts]
            removed = original_count - len(combined)
            if removed > 0:
                logger.info(f"🔍 MODULE 1 DEDUP: Removed {removed} samples matching Module 0 DB questions")

        if len(combined) >= limit:
            return combined

        left_to_generate = limit - len(combined)

        generated_samples = self._gpt_fallback_generate_samples(grade=grade, subject=subject, limit=left_to_generate, language=language, provider=provider, query=query, skill_focus=skill_focus)

        combined.extend(generated_samples)
        return combined

    def _merge_sample_sources(self, rag_samples: List[RetrievedSample], psql_samples: List[RetrievedSample], limit: int, exclude_question_texts: Optional[set] = None) -> List[RetrievedSample]:
        """Granularly merge RAG and PostgreSQL samples, removing duplicates and prioritizing quality."""
        combined = []
        seen_questions = set()

        # Initialize with Module 0 exclusions if provided
        if exclude_question_texts:
            seen_questions.update(exclude_question_texts)

        # Prioritize RAG samples first (they come from vector similarity)
        for sample in rag_samples:
            question_key = sample.question_text.strip().lower()[:100]  # Use first 100 chars as key
            if question_key not in seen_questions:
                combined.append(sample)
                seen_questions.add(question_key)
                if len(combined) >= limit:
                    break

        # Add PostgreSQL samples to fill remaining slots
        for sample in psql_samples:
            if len(combined) >= limit:
                break
            question_key = sample.question_text.strip().lower()[:100]
            if question_key not in seen_questions:
                combined.append(sample)
                seen_questions.add(question_key)

        return combined[:limit]


    def evaluate_and_update_samples(self, samples: List[RetrievedSample], grade: int, subject: str, query: str, skill_focus: str, provider: str, limit: int) -> List[RetrievedSample]:
        passed_samples = []
        try:
            class EvaluatedSample(BaseModel):
                sample: RetrievedSample
                is_appropriate: bool
                reason: str

            class EvaluationResponse(BaseModel):
                samples: List[EvaluatedSample]

            messages = [
                {"role": "system", "content": f"""You are an expert educational question validator evaluator for grade {grade} and subject {subject} and {skill_focus.replace('"', '')} requested questions based on the query {query.replace('"', '')}. The user will provide a list of samples and you will evaluate them based on the grade, subject, and skill focus. You will return the list of samples that are appropriate marked is_appropriate as True and the ones that are not appropriate marked as False."""},
                {"role": "user", "content": f"Samples: {samples}"}
            ]

            response = produce_structured_response(
                messages=messages,
                structure_model=EvaluationResponse,
                provider=provider,
                max_output_tokens=2048
            )

            response = to_dict(response)

            for sample in response["samples"]:
                if sample['is_appropriate']:
                    passed_samples.append(sample['sample'])

            return passed_samples

        except Exception as e:
            logger.warning(f"Evaluation failed: {e}, returning no samples")
            return passed_samples


    # ------------------------------------------------------
    # RAG retrieval using your DSPyMongoRAG (no other RAG code)
    # ------------------------------------------------------
    def _rag_retrieve(self, *, limit: int, subject: str, grade: int, language: str, skill_terms: List[str], skill_focus: str, query: str) -> List[RetrievedSample]:
        """
        Use DSPyMongoRAG with a retrieval-only stage to fetch passages/doc_ids,
        then hydrate minimal fields from the underlying collection.
        """
        # Let DSPy handle the sophisticated multi-stage process
        # Build retrieval stage with enhanced rewrite instructions
        retrieve_stage = self.rag.stage_retrieve(
            k=max(20, limit),  # Get more to filter for quality
            filters={},
            query_field="question",
            rewrite=True,
            rewrite_instructions=(
                f"Rewrite this query to find high-quality educational content in {language} for "
                f"{subject} at grade/level {grade}. Adapt terminology, cultural context, and "
                "educational frameworks appropriate to the target language and educational system. "
                "Focus on instructional content rather than bibliographies or metadata."
            ),
            instructions=(
                f"Package retrieved passages for {language} {subject} grade {grade}. "
                f"Put formatted passages in 'passages' field, document IDs in 'doc_ids' array."
            ),
            deterministic=True,  # Use deterministic mode to avoid JSON generation issues
        )

        # Stage 2: Curate educational content from retrieved passages
        curation_stage = DSPyMongoRAG.StageSpec(
            name="curate",
            input_model=DSPyMongoRAG.SelectedPassages,  # Takes output from retrieve stage
            output_model=DSPyMongoRAG.FinalAnswer,      # Outputs curated content
            sys_instructions=(
                f"From the retrieved passages, select high-quality educational content for {subject} "
                f"at grade {grade} in {language}. Focus on teaching materials, activities, and explanations. "
                f"Exclude bibliographies, URLs, and metadata. Put the curated content in 'answer' field, "
                f"document IDs in 'citations' array, and a confidence score (0.0-1.0) in 'confidence'."
            ),
            retrieval=None,  # No additional retrieval needed
            critic_instructions=(
                f"Check if content is educational for {subject} grade {grade} in {language}. "
                f"Ensure no bibliographies or URLs. Verify JSON has 'answer', 'citations', 'confidence' fields."
            ),
            rounds=2,
            max_tokens=500,
            temperature=0.2
        )

        # Stage 3: Structure content into learning samples with difficulty assessment
        structuring_stage = DSPyMongoRAG.StageSpec(
            name="structure",
            input_model=DSPyMongoRAG.FinalAnswer,       # Takes curated content
            output_model=DSPyMongoRAG.FinalAnswer,      # Outputs structured samples
            sys_instructions=(
                f"Create {limit} learning samples from the content for {subject} grade {grade} in {language}. "
                f"Format in 'answer' field as numbered text: '1. Question | Topic | Difficulty | Content\\n\\n2. ...' "
                f"Use difficulty levels: easy/medium/hard/expert. Include document IDs in 'citations', "
                f"confidence score in 'confidence'."
            ),
            retrieval=None,  # No additional retrieval needed
            critic_instructions=(
                f"Verify {limit} samples provided. Check JSON has 'answer' (string), 'citations' (array), 'confidence' (number)."
            ),
            rounds=2,
            max_tokens=1200,
            temperature=0.2
        )

        # Run multi-stage pipeline with all stages
        logger.debug(f"Running multi-stage RAG pipeline with query: '{query}'")

        stages = [retrieve_stage, curation_stage, structuring_stage]
        initial_input = self.rag.RetrievalInput(
            question=query,
            grade=grade,
            topic_hint=f"{subject} level {grade} {language} | skill: {skill_focus}"
        )

        try:
            import threading

            # Flag to track if RAG completed
            rag_completed = threading.Event()
            rag_result = [None]
            rag_error = [None]

            def run_rag_with_timeout():
                try:
                    rag_result[0] = self.rag.run(stages=stages, initial_input=initial_input)
                    rag_completed.set()
                except Exception as e:
                    rag_error[0] = e
                    rag_completed.set()

            # Start RAG in background thread
            rag_thread = threading.Thread(target=run_rag_with_timeout, daemon=True)
            rag_thread.start()

            # Wait up to 90 seconds for completion
            if rag_completed.wait(timeout=90):
                # RAG completed within timeout
                if rag_error[0]:
                    raise rag_error[0]
                final_result = rag_result[0]
                logger.info(f"Multi-stage RAG completed with {len(stages)} stages")
            else:
                # Timeout occurred
                logger.error(f"Multi-stage RAG timed out after 90 seconds")
                raise TimeoutError("RAG processing exceeded 90 second timeout")

        except TimeoutError as e:
            logger.error(f"Multi-stage RAG timed out: {e}")
            # Return a fallback FinalAnswer to prevent complete failure
            final_result = self.rag.FinalAnswer(
                answer=f"RAG processing timed out after 90 seconds",
                citations=[],
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Multi-stage RAG failed: {e}")
            # Return a fallback FinalAnswer to prevent complete failure
            final_result = self.rag.FinalAnswer(
                answer=f"Error during RAG processing: {str(e)}",
                citations=[],
                confidence=0.0
            )

        # Parse the final structured result
        if isinstance(final_result, self.rag.FinalAnswer):
            structured_content = final_result.answer
            logger.debug(f"Structured content ({len(structured_content)} chars): {structured_content[:200]}...")

            return self._parse_structured_samples(structured_content, subject, grade, language, limit)
        else:
            logger.warning(f"Unexpected result type: {type(final_result).__name__}")
            return []

    def _parse_structured_samples(
        self, structured_content: str, subject: str, grade: int, language: str, limit: int
    ) -> List[RetrievedSample]:
        """Parse AI-structured content into RetrievedSample objects."""
        samples = []

        # Split by numbered items or clear separators
        parts = []
        for separator in ["\n\n", "\n1.", "\n2.", "\n3.", "\n4.", "\n5."]:
            if separator in structured_content:
                parts = [p.strip() for p in structured_content.split(separator) if p.strip()]
                break

        if not parts:
            # Fallback: treat entire content as single sample
            parts = [structured_content.strip()]

        logger.debug(f"Parsed {len(parts)} content parts from structured output")

        for part in parts[:limit]:
            if len(part) < 30:  # Skip very short parts
                continue

            # Clean up numbering prefixes and parse DSPy structured format
            content = re.sub(r'^\d+\.\s*', '', part.strip())

            # Try to parse DSPy format: [Question] | [Topic] | [Difficulty] | [Content]
            content_parts = [p.strip() for p in content.split('|')]
            if len(content_parts) >= 4:
                question_text = content_parts[0]
                topic = content_parts[1]
                difficulty = content_parts[2].lower()
                main_content = ' | '.join(content_parts[3:])
                full_content = f"{question_text} {main_content}"
            else:
                # Fallback to original content
                question_text = content
                topic = self._extract_topic_from_content(content)
                difficulty = "medium"  # Default if DSPy parsing fails
                full_content = content

            # Guard against stage error strings bleeding through
            if "failed to produce valid FinalAnswer JSON" in full_content:
                logger.warning("Stage error detected in structured content; dropping item")
                continue

            samples.append(
                RetrievedSample(
                    question_text=full_content[:600].strip(),
                    subject_area=subject,
                    grade=grade,
                    topic=topic,
                    difficulty=difficulty,
                    language=language,
                    answer=None,
                    explanation=None,
                    source="Multi-Stage RAG (DSPy)",
                )
            )

        logger.info(f"Created {len(samples)} RetrievedSample objects from structured content")
        return samples

    def _parse_skill_title_with_dspy(self, skill_title_combined: str, grade: int, subject: str, language: str) -> Dict[str, Any]:
        """Use DSPy to intelligently parse skill title instructions."""
        try:
            # Parse the combined skill title format: skill_title | unit_name | lesson_title | standard_description | instructions
            parts = [p.strip() if p.strip() != "None" else "" for p in (skill_title_combined or "").split('|')]

            skill_title = parts[0] if len(parts) > 0 else ""
            unit_name = parts[1] if len(parts) > 1 else ""
            lesson_title = parts[2] if len(parts) > 2 else ""
            standard_description = parts[3] if len(parts) > 3 else ""
            instructions = parts[4] if len(parts) > 4 else ""

            result = self.skill_parser(
                skill_title=skill_title,
                unit_name=unit_name,
                lesson_title=lesson_title,
                standard_description=standard_description,
                sys_instructions=instructions,
                grade=str(grade),
                subject=subject,
                language=language
            )

            # Parse the JSON response
            parsed_data = parse_json(result.parsed_components) or {}

            # Store structured components
            components = {
                'skill_title': skill_title,
                'unit_name': unit_name,
                'lesson_title': lesson_title,
                'standard_description': standard_description,
                'instructions': instructions,
                'focus_topic': parsed_data.get('focus_topic', skill_title or subject),
                'learning_objectives': parsed_data.get('learning_objectives', []),
                'key_concepts': parsed_data.get('key_concepts', []),
                'search_terms': parsed_data.get('search_terms', []),
                'priority_elements': parsed_data.get('priority_elements', [])
            }

            logger.debug(f"DSPy parsed skill: {skill_title} | Unit: {unit_name} | Lesson: {lesson_title}")
            return components

        except Exception as e:
            logger.warning(f"DSPy skill parsing failed: {e}, using fallback")
            return self._fallback_skill_parsing(skill_title_combined, subject)

    def _fallback_skill_parsing(self, skill_title_combined: str, subject: str) -> Dict[str, Any]:
        """Simple fallback parsing when DSPy fails."""
        if not skill_title_combined:
            return {
                'skill_title': '',
                'unit_name': '',
                'lesson_title': '',
                'standard_description': '',
                'instructions': '',
                'focus_topic': subject,
                'learning_objectives': [],
                'key_concepts': [],
                'search_terms': [subject]
            }

        # Parse server.py format: skill_title | unit_name | lesson_title | standard_description | instructions
        parts = [p.strip() if p.strip() != "None" else "" for p in skill_title_combined.split('|')]

        return {
            'skill_title': parts[0] if len(parts) > 0 else '',
            'unit_name': parts[1] if len(parts) > 1 else '',
            'lesson_title': parts[2] if len(parts) > 2 else '',
            'standard_description': parts[3] if len(parts) > 3 else '',
            'instructions': parts[4] if len(parts) > 4 else '',
            'focus_topic': parts[0] if len(parts) > 0 else subject,
            'learning_objectives': [parts[4]] if len(parts) > 4 and parts[4] else [],
            'key_concepts': [parts[0]] if len(parts) > 0 and parts[0] else [],
            'search_terms': [p for p in parts[:3] if p]
        }

    def _generate_skill_aware_query(self, components: Dict[str, Any], grade: int, subject: str, language: str) -> str:
        """Use DSPy to generate optimized query based on skill components."""
        try:
            result = self.content_retriever(
                skill_title=components.get('skill_title', ''),
                unit_name=components.get('unit_name', ''),
                lesson_title=components.get('lesson_title', ''),
                standard_description=components.get('standard_description', ''),
                sys_instructions=components.get('instructions', ''),
                focus_topic=components.get('focus_topic', ''),
                grade=str(grade),
                subject=subject,
                language=language
            )

            optimized_query = result.optimized_query.strip()
            logger.debug(f"DSPy generated skill-aware query: {optimized_query[:100]}...")
            return optimized_query

        except Exception as e:
            logger.warning(f"DSPy query generation failed: {e}, using fallback")
            return self._fallback_query_generation(components, grade, subject)

    def _fallback_query_generation(self, components: Dict[str, Any], grade: int, subject: str) -> str:
        """Fallback query generation when DSPy fails."""
        skill_title = components.get('skill_title', '')
        unit_name = components.get('unit_name', '')
        lesson_title = components.get('lesson_title', '')
        instructions = components.get('instructions', '')

        query_parts = [f"educational content"]
        if skill_title:
            query_parts.append(skill_title)
        if unit_name:
            query_parts.append(unit_name)
        if lesson_title:
            query_parts.append(lesson_title)
        if instructions:
            query_parts.append(instructions)

        query_parts.extend([subject, f"grade {grade}"])
        return ' '.join(query_parts)

    def _extract_topic_from_content(self, content: str) -> str:
        """Extract topic from content using simple heuristics."""
        # Take first meaningful sentence or phrase
        sentences = content.split('.')[0:2]
        return ' '.join(sentences).strip()[:100] or "General"


    # ----------------------------------------
    # Fallback generator using solve_with_llm
    # ----------------------------------------

    def _gpt_fallback_generate_samples(
        self,
        *,
        grade: int,
        subject: str,
        limit: int,
        language: str,
        provider: str = "openai",
        query: str = None,
        skill_focus: str = None,
    ) -> List[RetrievedSample]:
        """
        Enhanced GPT fallback for generating high-quality educational samples.
        """
        sys_prompt = f"""You are an expert educational content creator specializing in {subject} for grade {grade}.
            Generate high-quality educational Q&A items in {language}.
            Output valid JSON only. No explanations, no code fences."""

        user_prompt = f"""Generate exactly {limit} educational Q&A items for:
            - Grade Level: {grade} [CRITICAL: Must match this grade level exactly]
            - Subject: {subject}
            - Language: {language}
            {f'- Skill Focus: {skill_focus} [CRITICAL: All questions MUST directly address this skill]' if skill_focus else ''}
            {f'- Query Context: {query} [CRITICAL: Questions should align with this specific context]' if query else ''}

            CRITICAL Requirements:
            1. GRADE APPROPRIATENESS: Questions MUST be exactly right for grade {grade} - not easier, not harder
            2. SKILL ALIGNMENT: Every question MUST directly practice or assess {skill_focus if skill_focus else 'the core subject skills'}
            3. QUERY RELEVANCE: Questions should directly relate to: {query if query else 'general curriculum'}
            4. CONCRETE PROBLEMS: Include specific values, not just variables or placeholders
            5. VARIED PROBLEM TYPES: Mix different types of problems appropriate for the topic
            6. CLEAR SOLUTIONS: Step-by-step solutions with exact answers where applicable

            Output this EXACT JSON structure:
            {{
            "questions": [
                {{
                "question_text": "Specific problem with concrete values appropriate for grade {grade}",
                "answer": "Complete, accurate answer with specific values",
                "explanation": "Step-by-step solution showing the work",
                "topic": "Specific topic within {subject}",
                "difficulty": "easy|medium|hard based on cognitive complexity for grade {grade}"
                }}
            ]
            }}"""

        try:
            raw = solve_with_llm(
                messages=format_messages_for_api(sys_prompt, user_prompt),
                max_tokens=4000,
                provider=provider,
                temperature=0.7,
            )

            # Robust parsing
            if isinstance(raw, str):
                import json
                try:
                    raw = json.loads(raw)
                except:
                    logger.warning("Failed to parse GPT response as JSON")
                    raw = {}

            items = raw.get("questions", []) if isinstance(raw, dict) else []

            # Validate and create samples
            out: List[RetrievedSample] = []
            for idx, item in enumerate(items[:limit]):
                question_text = str(item.get("question_text", "")).strip()
                answer = str(item.get("answer", "")).strip()

                if not question_text or not answer:
                    logger.warning(f"Skipping item {idx}: missing question or answer")
                    continue

                difficulty = str(item.get("difficulty", "medium")).lower()
                if difficulty not in ["easy", "medium", "hard"]:
                    difficulty = "medium"

                out.append(
                    RetrievedSample(
                        question_text=question_text,
                        subject_area=subject,
                        grade=grade,
                        topic=str(item.get("topic", subject)).strip() or subject,
                        difficulty=difficulty,
                        language=language,
                        answer=answer,
                        explanation=str(item.get("explanation", "")).strip() or answer,
                        source="GPT-generated",
                    )
                )

            if len(out) < limit:
                logger.warning(f"GPT fallback generated only {len(out)}/{limit} samples")

            return out

        except Exception as e:
            logger.error(f"GPT fallback generation failed: {e}")
            return []

    def compile_rag_pipeline(self, training_examples: List[dspy.Example], max_demos: int = 12,
                            use_mipro: bool = False) -> bool:
        """
        Compile the RAG pipeline using BootstrapFewShot or MIPROv2.

        Args:
            training_examples: List of dspy.Example objects with .with_inputs('question', 'grade')
            max_demos: Maximum number of bootstrapped demonstrations (default: 12)
            use_mipro: Use MIPROv2 instead of BootstrapFewShot (requires 100+ examples)

        Returns:
            bool: True if compilation succeeded and saved, False otherwise

        Example:
            >>> m1 = Module1RAGRetriever()
            >>> examples = [
            ...     dspy.Example(question="What is 5 × 3?", grade=3, answer="15").with_inputs('question', 'grade'),
            ...     # ... add 50-100 more examples
            ... ]
            >>> # Basic compilation
            >>> success = m1.compile_rag_pipeline(examples)
            >>> # Advanced: MIPROv2 (better with 100+ examples)
            >>> success = m1.compile_rag_pipeline(examples, use_mipro=True)
        """
        try:
            from src.dspy_improvements import RAGCompiler, RAGMetric

            logger.info(f"🔧 Starting RAG pipeline compilation with {len(training_examples)} examples...")

            # Validate training set size
            if use_mipro and len(training_examples) < 50:
                logger.warning("⚠️ MIPROv2 works best with 100+ examples.")
                logger.info("Falling back to BootstrapFewShot for better results")
                use_mipro = False
            elif len(training_examples) < 10:
                logger.warning("⚠️ Less than 10 training examples. Compilation may not be effective.")
                logger.warning("   Collect at least 50-100 examples for best results.")

            # Set up compiler
            compiler = RAGCompiler(
                artifacts_dir="artifacts/dspy_compiled",
                metric=RAGMetric(min_confidence=0.7, require_citations=True)
            )

            # Compile with selected optimizer
            if use_mipro:
                logger.info("🔄 Running MIPROv2 compilation (joint instruction+demo optimization)...")
                compiled = compiler.compile_with_mipro(
                    module=self.rag,
                    trainset=training_examples,
                    num_candidates=10,
                    max_bootstrapped_demos=max_demos
                )
            else:
                logger.info("🔄 Running BootstrapFewShot compilation...")
                compiled = compiler.compile_with_bootstrap(
                    module=self.rag,
                    trainset=training_examples,
                    max_bootstrapped_demos=max_demos
                )

            # Evaluate on held-out set
            logger.info("📊 Evaluating compiled pipeline...")
            evalset = training_examples[:min(20, len(training_examples)//5)]  # Hold out 20% or 20 examples

            metrics = compiler.evaluate(compiled, evalset, baseline=self.rag)

            logger.info(f"📈 Compilation Results:")
            logger.info(f"   Baseline: {metrics.baseline_score:.3f}")
            logger.info(f"   Compiled: {metrics.compiled_score:.3f}")
            logger.info(f"   Improvement: {metrics.improvement:.1%}")

            # Save if improvement threshold met
            if metrics.improvement > 0.05:  # 5% improvement threshold
                compiler.save_compiled(compiled, "rag_pipeline", metadata=metrics.__dict__)
                logger.info("✅ Compiled pipeline saved to artifacts/dspy_compiled/rag_pipeline/")
                logger.info("   To use it, reinitialize Module1RAGRetriever(enable_compilation=True)")
                return True
            else:
                logger.warning("⚠️ No significant improvement, keeping baseline")
                logger.warning("   Consider:")
                logger.warning("   - Collecting more training examples")
                logger.warning("   - Improving example quality")
                logger.warning("   - Adjusting compilation parameters")
                return False

        except Exception as e:
            logger.error(f"❌ Compilation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
