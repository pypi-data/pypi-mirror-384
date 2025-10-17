#!/usr/bin/env python3
"""
PostgreSQL-based Question Retriever for Module 1 V1.1

Retrieves sample questions from Supabase PostgreSQL database using:
1. Direct match on skills/standards (exact filtering)
2. Vector similarity search (parallel)
3. Quality filtering (>=6.0 for textbook, no filter for athena)
4. DI format extraction (use direct_instruction_raw if available, fallback to old method)
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase import create_client, Client
from dotenv import load_dotenv

from src.embeddings import Embeddings

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class RetrievedSample:
    """Structured output for retrieved samples."""
    question_text: str
    subject_area: str
    grade: int
    topic: str
    difficulty: str
    language: str
    answer: Optional[str] = None
    explanation: Optional[str] = None
    source: str = "PostgreSQL"
    di_content: Optional[str] = None  # Direct Instruction content
    direct_instruction_raw: Optional[str] = None  # Raw DI markdown
    relevance_score: Optional[float] = None  # 0.0-1.0 relevance score from Module 1 curation


class PSQLQuestionRetriever:
    """
    PostgreSQL-based question retriever using Supabase.

    Features:
    - Direct skill/standard matching
    - Vector similarity search (parallel)
    - Quality filtering (textbook: >=6.0, athena: no filter)
    - DI content extraction (prefer DB, fallback to RAG)
    """

    def __init__(self):
        """Initialize Supabase client and embeddings."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not all([self.supabase_url, self.supabase_key]):
            logger.warning("⚠️ PSQLQuestionRetriever: SUPABASE_URL and SUPABASE_SERVICE_KEY not set - retrieval will be disabled")
            self.supabase = None
            self.embeddings = None

            return

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.embeddings = Embeddings()

        logger.info("✓ PSQLQuestionRetriever initialized with Supabase")

    def retrieve_samples(
        self,
        grade: int,
        subject: str,
        limit: int = 10,
        skill_id: Optional[str] = None,
        skill_title: Optional[str] = None,
        unit_name: Optional[str] = None,
        lesson_title: Optional[str] = None,
        substandard_description: Optional[str] = None,
        language: str = "arabic",
        exclude_question_texts: Optional[set] = None,
    ) -> List[RetrievedSample]:
        """
        Retrieve sample questions from PostgreSQL using hybrid approach.

        Strategy:
        1. Direct match: Filter by grade, subject, skill/standard (if provided)
        2. Vector search: Parallel vector similarity search
        3. Merge and deduplicate results
        4. Quality filter: textbook >=6.0, athena no filter
        5. Extract DI content (prefer DB, fallback to RAG)
        6. Return top `limit` samples

        Args:
            grade: Target grade level
            subject: Subject area (e.g., "mathematics")
            limit: Maximum number of samples to return (default: 10)
            skill_id: Skill/substandard ID for exact matching (e.g., CCSS.MATH.CONTENT.3.OA.A.2+2)
            skill_title: Skill title for filtering (e.g., "Rounding")
            unit_name: Unit name for context (e.g., "Place Value and Rounding")
            lesson_title: Lesson title for context (e.g., "Round to the nearest 10 or 100.")
            substandard_description: Substandard description for specific matching
            language: Target language
            exclude_question_texts: Set of question texts to exclude

        Returns:
            List of RetrievedSample objects
        """
        # Check if Supabase is configured
        if self.supabase is None:
            logger.warning("⚠️ PSQLQuestionRetriever not configured - returning empty list")
            return []

        exclude_question_texts = exclude_question_texts or set()

        # Build search query for vector search
        search_query = self._build_search_query(
            grade=grade,
            subject=subject,
            skill_title=skill_title,
            unit_name=unit_name,
            lesson_title=lesson_title,
            substandard_description=substandard_description,
            skill_id=skill_id
        )

        logger.info("="*80)
        logger.info(f"🔍 RETRIEVAL START: grade={grade}, subject={subject}, limit={limit}")
        logger.info(f"   Skill ID: {skill_id or 'None'}")
        logger.info(f"   Skill Title: {skill_title or 'None'}")
        logger.info(f"   Unit: {unit_name or 'None'}")
        logger.info(f"   Lesson: {lesson_title or 'None'}")
        logger.info(f"   Substandard Description: {substandard_description or 'None'}")
        logger.info(f"   Language: {language}")
        logger.info(f"   Exclude count: {len(exclude_question_texts)}")
        logger.info(f"   Search query: {search_query}")
        logger.info("="*80)

        # Execute retrieval strategies in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            direct_future = executor.submit(
                self._direct_match_retrieval,
                grade=grade,
                subject=subject,
                skill_id=skill_id,
                skill_title=skill_title,
                unit_name=unit_name,
                lesson_title=lesson_title,
                substandard_description=substandard_description,
                limit=limit
            )

            vector_future = executor.submit(
                self._vector_search_retrieval,
                query=search_query,
                grade=grade,
                limit=limit,
                skill_id=skill_id,
                lesson_title=lesson_title,
                substandard_description=substandard_description,
                unit_name=unit_name
            )

            # Collect results
            direct_results = []
            vector_results = []

            for future in as_completed([direct_future, vector_future]):
                try:
                    if future == direct_future:
                        direct_results = future.result()
                        logger.info(f"  ✓ Direct match: {len(direct_results)} results")
                        if direct_results:
                            logger.info(f"     First 3 IDs: {[r.get('id', 'N/A')[:8] for r in direct_results[:3]]}")
                            logger.info(f"     Sources: {[r.get('source_type', 'N/A') for r in direct_results[:3]]}")
                            logger.info(f"     Quality: {[r.get('quality_score', 'N/A') for r in direct_results[:3]]}")
                    else:
                        vector_results = future.result()
                        logger.info(f"  ✓ Vector search: {len(vector_results)} results")
                        if vector_results:
                            logger.info(f"     First 3 IDs: {[r.get('id', 'N/A')[:8] for r in vector_results[:3]]}")
                            similarity_scores = [f"{r.get('_similarity_score', 0):.3f}" for r in vector_results[:3]]
                            logger.info(f"     Similarity: {similarity_scores}")
                            logger.info(f"     Sources: {[r.get('source_type', 'N/A') for r in vector_results[:3]]}")
                except Exception as e:
                    logger.error(f"  ✗ Retrieval failed: {e}")

        # Merge and deduplicate results
        logger.info(f"📊 Merging results...")
        merged_results = self._merge_and_deduplicate(
            direct_results,
            vector_results,
            exclude_texts=exclude_question_texts
        )
        logger.info(f"   Merged: {len(merged_results)} unique results")

        # Apply quality filtering
        logger.info(f"🔍 Applying quality filter...")
        filtered_results = self._apply_quality_filter(merged_results)
        logger.info(f"   Filtered: {len(filtered_results)} results passed quality check")

        # Convert to RetrievedSample objects
        logger.info(f"📝 Converting to samples (limit={limit})...")
        samples = []
        for idx, result in enumerate(filtered_results[:limit], 1):
            logger.info(f"   [{idx}/{min(limit, len(filtered_results))}] Processing: {result.get('id', 'N/A')[:8]}...")
            sample = self._convert_to_sample(result)
            logger.info(f"       Question: {sample.question_text[:80]}...")
            logger.info(f"       Source: {sample.source}")
            logger.info(f"       Grade: {sample.grade}, Difficulty: {sample.difficulty}")
            samples.append(sample)

        logger.info("="*80)
        logger.info(f"📦 RETRIEVAL COMPLETE: {len(samples)} samples returned")
        logger.info(f"   Sources breakdown: {dict((s.source, [s.source for s in samples].count(s.source)) for s in samples)}")
        logger.info("="*80)
        return samples

    def _build_search_query(
        self,
        grade: int,
        subject: str,
        skill_title: Optional[str],
        unit_name: Optional[str],
        lesson_title: Optional[str],
        substandard_description: Optional[str],
        skill_id: Optional[str]
    ) -> str:
        """Build optimized search query for vector search using separate skill fields."""
        parts = [
            f"Grade {grade}",
            subject
        ]

        # Prioritize more specific fields for better vector search
        if substandard_description:  # Most specific
            parts.append(substandard_description)
        elif lesson_title:  # Fallback to lesson title
            parts.append(lesson_title)

        if unit_name:
            parts.append(unit_name)

        if skill_title:
            parts.append(skill_title)

        if skill_id:
            parts.append(f"Standard {skill_id}")

        return " ".join(parts)

    def _direct_match_retrieval(
        self,
        grade: int,
        subject: str,
        skill_id: Optional[str],
        skill_title: Optional[str],
        unit_name: Optional[str],
        lesson_title: Optional[str],
        substandard_description: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Direct match retrieval using exact filters with separate skill fields.

        Strategy (priority order):
        1. Exact match on skill_id (substandard_id) if provided
        2. Fuzzy match on substandard_description (most specific)
        3. Fuzzy match on lesson_title
        4. Fuzzy match on skill_title (least specific)
        5. Optional: filter by unit_name for additional specificity

        Filters:
        - grade (exact)
        - subject (case-insensitive contains)
        - skill fields (as described above)
        """
        logger.info(f"🎯 Direct match retrieval starting...")
        logger.info(f"   Grade: {grade}, Subject: {subject}")
        logger.info(f"   Skill ID: {skill_id or 'None'}")
        logger.info(f"   Skill Title: {skill_title or 'None'}")
        logger.info(f"   Unit: {unit_name or 'None'}")
        logger.info(f"   Lesson: {lesson_title or 'None'}")
        logger.info(f"   Substandard Desc: {substandard_description or 'None'}")

        try:
            query = self.supabase.table("extracted_questions").select("*")

            # Grade filter (exact)
            query = query.eq("grade", grade)

            # Subject filter (case-insensitive)
            if subject:
                query = query.ilike("subject", f"%{subject}%")

            # Skill matching strategy - hierarchical filtering with specificity prioritization
            # Strategy: Use most specific filters available, avoid diluting with broad filters
            skill_filters = []

            # 1. Always try exact match on skill_id if provided
            if skill_id:
                skill_filters.append(f"substandard_id.eq.{skill_id}")
                logger.info(f"   Adding EXACT match filter: substandard_id={skill_id}")

            # 2. If we have substandard_description (very specific), use ONLY that + skill_id
            #    Don't add lesson_title or unit_name as they're too broad
            if substandard_description:
                skill_filters.append(f"substandard_description.ilike.%{substandard_description}%")
                logger.info(f"   Adding FUZZY match filter: substandard_description LIKE '{substandard_description}'")
            # 3. Else if we have lesson_title (moderately specific), use that
            #    Don't add unit_name as it's too broad
            elif lesson_title:
                skill_filters.append(f"lesson_title.ilike.%{lesson_title}%")
                logger.info(f"   Adding FUZZY match filter: lesson_title LIKE '{lesson_title}'")
            # 4. Else if we have unit_name (contextual), use that
            elif unit_name:
                skill_filters.append(f"unit_name.ilike.%{unit_name}%")
                logger.info(f"   Adding FUZZY match filter: unit_name LIKE '{unit_name}'")
            # 5. Else if we have skill_title (least specific), use that
            elif skill_title:
                skill_filters.append(f"lesson_title.ilike.%{skill_title}%")
                skill_filters.append(f"substandard_description.ilike.%{skill_title}%")
                logger.info(f"   Adding FUZZY match filter: lesson_title/substandard_description LIKE '{skill_title}'")

            # Apply combined OR filter if any skill fields provided
            if skill_filters:
                or_filter = ",".join(skill_filters)
                logger.info(f"   Final OR filter: {len(skill_filters)} conditions")
                query = query.or_(or_filter)
            else:
                logger.warning(f"   No skill filters provided, returning grade/subject matches only")

            # Order by quality score (descending) and limit
            query = query.order("quality_score", desc=True)
            query = query.limit(limit * 2)  # Get extra for deduplication

            logger.info(f"   Executing query with limit={limit * 2}...")
            response = query.execute()
            results = response.data if response.data else []

            logger.info(f"   ✓ Got {len(results)} results from direct match")
            if results:
                quality_score = results[0].get('quality_score')
                quality_str = f"{quality_score:.2f}" if quality_score is not None else "N/A"
                logger.info(f"   Top result: grade={results[0].get('grade')}, "
                          f"domain={results[0].get('domain')}, "
                          f"quality={quality_str}")

            return results

        except Exception as e:
            logger.error(f"   ✗ Direct match retrieval failed: {e}")
            return []

    def _fetch_vector_candidates(
        self,
        grade: int,
        filters: Dict[str, str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidate questions for vector search with optional filters.

        Args:
            grade: Grade level filter
            filters: Additional filters (substandard_id, lesson_title, unit_name)
            limit: Maximum candidates to fetch

        Returns:
            List of question dictionaries with dense_vector field
        """
        try:
            query = self.supabase.table("extracted_questions").select("*")
            query = query.eq("grade", grade)
            query = query.not_.is_("dense_vector", "null")

            # Apply additional filters
            if "substandard_id" in filters:
                query = query.eq("substandard_id", filters["substandard_id"])
            if "substandard_description" in filters:
                query = query.ilike("substandard_description", f"%{filters['substandard_description']}%")
            if "lesson_title" in filters:
                query = query.ilike("lesson_title", f"%{filters['lesson_title']}%")
            if "unit_name" in filters:
                query = query.ilike("unit_name", f"%{filters['unit_name']}%")

            query = query.order("quality_score", desc=True)
            query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.warning(f"   Error fetching candidates: {e}")
            return []

    def _vector_search_retrieval(
        self,
        query: str,
        grade: int,
        limit: int,
        skill_id: Optional[str] = None,
        lesson_title: Optional[str] = None,
        substandard_description: Optional[str] = None,
        unit_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search using embeddings with progressive broadening.

        Strategy:
        1. Try narrow search (skill_id + grade) - most specific
        2. If insufficient, broaden to substandard_description + grade - very specific
        3. If insufficient, broaden to lesson_title + grade - broad topic
        4. If insufficient, broaden to unit_name + grade - unit level
        5. If insufficient, fall back to grade only - broadest

        Uses:
        - Query embedding (OpenAI text-embedding-3-small, 1536 dims)
        - Cosine similarity search on dense_vector column
        - Progressive filter broadening
        """
        logger.info(f"🔍 Vector search retrieval starting...")
        logger.info(f"   Query: {query}")
        logger.info(f"   Grade: {grade}, Limit: {limit}")

        try:
            # Generate query embedding (use OpenAI to match DB schema - 1536 dimensions)
            logger.info(f"   Generating query embedding...")
            query_vector = self.embeddings.get_openai_embedding(query)
            logger.info(f"   ✓ Generated embedding (dim={len(query_vector)})")

            # Progressive broadening strategy
            search_configs = []

            # Level 1: Most specific - skill_id match
            if skill_id:
                search_configs.append({
                    "name": "skill_id exact match",
                    "filters": {"substandard_id": skill_id},
                    "limit": limit * 3
                })

            # Level 2: Substandard description fuzzy match (very specific)
            if substandard_description:
                search_configs.append({
                    "name": "substandard_description fuzzy match",
                    "filters": {"substandard_description": substandard_description},
                    "limit": limit * 3
                })

            # Level 3: Lesson title fuzzy match (broad topic)
            if lesson_title:
                search_configs.append({
                    "name": "lesson_title fuzzy match",
                    "filters": {"lesson_title": lesson_title},
                    "limit": limit * 4
                })

            # Level 4: Unit name fuzzy match (unit level)
            if unit_name:
                search_configs.append({
                    "name": "unit_name fuzzy match",
                    "filters": {"unit_name": unit_name},
                    "limit": limit * 5
                })

            # Level 5: Grade only (broadest fallback)
            search_configs.append({
                "name": "grade only (fallback)",
                "filters": {},
                "limit": limit * 6
            })

            # Try each search level until we get enough results
            all_candidates = []
            for config in search_configs:
                logger.info(f"   → Trying level: {config['name']} (target: {limit * 2} results)")

                candidates = self._fetch_vector_candidates(
                    grade=grade,
                    filters=config["filters"],
                    limit=config["limit"]
                )

                logger.info(f"      Got {len(candidates)} candidates from {config['name']}")

                # Add new candidates (avoid duplicates by content_hash)
                seen_hashes = {c.get("content_hash") for c in all_candidates if c.get("content_hash")}
                new_candidates = [c for c in candidates if c.get("content_hash") not in seen_hashes]
                all_candidates.extend(new_candidates)

                logger.info(f"      Total unique candidates: {len(all_candidates)}")

                # Stop if we have enough
                if len(all_candidates) >= limit * 2:
                    logger.info(f"   ✓ Sufficient candidates found at level: {config['name']}")
                    break

            results = all_candidates
            logger.info(f"   ✓ Got {len(results)} total candidates with vectors")

            # Calculate cosine similarity for each result
            logger.info(f"   Calculating cosine similarities...")
            import numpy as np
            from numpy import dot
            from numpy.linalg import norm

            def cosine_similarity(vec1, vec2):
                return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

            # Score and sort results
            scored_results = []
            for result in results:
                if result.get("dense_vector"):
                    # Parse vector from string to numpy array
                    dense_vec = result["dense_vector"]
                    if isinstance(dense_vec, str):
                        # Remove brackets and parse as floats
                        dense_vec = np.array(eval(dense_vec))
                    elif isinstance(dense_vec, list):
                        dense_vec = np.array(dense_vec)

                    similarity = cosine_similarity(query_vector, dense_vec)
                    result["_similarity_score"] = similarity
                    scored_results.append(result)

            logger.info(f"   ✓ Scored {len(scored_results)} results")

            # Sort by similarity
            scored_results.sort(key=lambda x: x.get("_similarity_score", 0), reverse=True)

            if scored_results:
                top_similarities = [f"{r['_similarity_score']:.3f}" for r in scored_results[:3]]
                logger.info(f"   Top 3 similarities: {top_similarities}")

            final_results = scored_results[:limit * 2]
            logger.info(f"   ✓ Returning top {len(final_results)} results")
            return final_results

        except Exception as e:
            logger.error(f"   ✗ Vector search retrieval failed: {e}")
            return []

    def _merge_and_deduplicate(
        self,
        direct_results: List[Dict],
        vector_results: List[Dict],
        exclude_texts: set
    ) -> List[Dict]:
        """
        Merge results from direct match and vector search, removing duplicates.

        Priority:
        1. Direct match results (higher priority)
        2. Vector search results (fill remaining slots)

        Deduplication by:
        - content_hash (unique identifier)
        - question text (if not in exclude_texts)
        """
        logger.info(f"🔀 Merging and deduplicating...")
        logger.info(f"   Direct: {len(direct_results)}, Vector: {len(vector_results)}, Excluded: {len(exclude_texts)}")

        seen_hashes = set()
        seen_questions = exclude_texts.copy()
        merged = []

        # Add direct match results first (higher priority)
        direct_added = 0
        for result in direct_results:
            content_hash = result.get("content_hash")
            question_text = result.get("question_en") or result.get("question_ar") or ""

            if content_hash and content_hash not in seen_hashes:
                if question_text not in seen_questions:
                    merged.append(result)
                    seen_hashes.add(content_hash)
                    seen_questions.add(question_text)
                    direct_added += 1

        logger.info(f"   Added {direct_added} from direct match")

        # Add vector search results (fill remaining)
        vector_added = 0
        for result in vector_results:
            content_hash = result.get("content_hash")
            question_text = result.get("question_en") or result.get("question_ar") or ""

            if content_hash and content_hash not in seen_hashes:
                if question_text not in seen_questions:
                    merged.append(result)
                    seen_hashes.add(content_hash)
                    seen_questions.add(question_text)
                    vector_added += 1

        logger.info(f"   Added {vector_added} from vector search")
        logger.info(f"   ✓ Total merged: {len(merged)} unique results")
        return merged

    def _apply_quality_filter(self, results: List[Dict]) -> List[Dict]:
        """
        Apply quality filtering based on source type.

        Rules:
        - textbook_pdf: quality_score >= 6.0
        - athena_api: no quality filter
        - curriculum_generated: quality_score >= 6.0
        """
        logger.info(f"🎯 Applying quality filter to {len(results)} results...")

        source_counts = {}
        filtered = []

        for result in results:
            source_type = result.get("source_type", "")
            quality_score = result.get("quality_score")

            # Count sources
            source_counts[source_type] = source_counts.get(source_type, 0) + 1

            # Athena questions: no quality filter
            if source_type == "athena_api":
                filtered.append(result)
            # Textbook/generated: require quality >= 6.0
            elif quality_score is not None and quality_score >= 6.0:
                filtered.append(result)
            # No quality score: include if not textbook
            elif quality_score is None and source_type != "textbook_pdf":
                filtered.append(result)

        logger.info(f"   Input sources: {source_counts}")
        logger.info(f"   ✓ Passed: {len(filtered)}/{len(results)} results")
        return filtered

    def _convert_to_sample(self, result: Dict) -> RetrievedSample:
        """Convert database result to RetrievedSample object."""
        # Determine language
        language = result.get("language", "arabic")
        if language == "both":
            language = "arabic"  # Default to arabic for bilingual

        # Extract question and answer based on language
        if language == "arabic" or language == "ar":
            question_text = result.get("question_ar") or result.get("question_en") or ""
            answer = result.get("answer_ar") or result.get("answer_en")
            explanation = result.get("explanation_ar") or result.get("explanation_en")
        else:
            question_text = result.get("question_en") or result.get("question_ar") or ""
            answer = result.get("answer_en") or result.get("answer_ar")
            explanation = result.get("explanation_en") or result.get("explanation_ar")

        return RetrievedSample(
            question_text=question_text,
            subject_area=result.get("subject", "mathematics"),
            grade=result.get("grade", 5),
            topic=result.get("domain") or result.get("substandard_description") or "General",
            difficulty=result.get("difficulty", "medium"),
            language=language,
            answer=answer,
            explanation=explanation,
            source=f"PostgreSQL ({result.get('source_type', 'unknown')})",
            direct_instruction_raw=result.get("direct_instruction_raw")
        )

