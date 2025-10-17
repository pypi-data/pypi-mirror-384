# dspy_mongo_rag.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Type, Callable, Union
import json
import re
import threading
import time
import logging
from functools import wraps

import dspy
from pydantic import BaseModel, ValidationError, Field
from langchain_mongodb import MongoDBAtlasVectorSearch
from src.llms import dspy_lm as lm

from src.utils.json_repair import parse_json
from src.utils.vector_store import get_vector_store

# Import DSPy improvements
from src.dspy_improvements import (
    cache_rewrite, cache_search,
    get_budget, AdaptiveTokenBudget,
    hybrid_search, ScoredDoc,
)

logger = logging.getLogger(__name__)


def timeout(seconds):
    """Decorator to add timeout to a function using threading.Timer (works in threads)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds")]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                # Thread is still running, timeout occurred
                raise TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds")

            if isinstance(result[0], Exception):
                raise result[0]

            return result[0]
        return wrapper
    return decorator


class DSPyMongoRAG:
    """
    One-class DSPy RAG engine (Mongo via LangChain's MongoDBAtlasVectorSearch).
    - Typed multi-stage pipeline (N stages)
    - Optional retrieval per stage (Atlas Vector Search)
    - Hidden-CoT + Critic→Revise repair
    - Strong JSON contracts via Pydantic
    - Uses external `parse_json` for resilient parsing
    - ⚠ LLM is NOT stored on the instance; pass `lm=` to `run`/`run_easy`/`easy_answer`.

    Initialize with either:
      - a ready `vector_store=MongoDBAtlasVectorSearch`, or
      - database parameters to obtain one via `get_vector_store(...)`.
    """

    # ----------------------------
    # 1) Base doc + retriever API
    # ----------------------------

    class Doc(BaseModel):
        id: str
        text: str
        meta: Dict[str, Any] = {}

    class Retriever(Protocol):
        def search(self, query: str, *, k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List["DSPyMongoRAG.Doc"]: ...
        def format_passages(self, docs: List["DSPyMongoRAG.Doc"]) -> str: ...

    class _SimpleFormatterMixin:
        def format_passages(self, docs: List["DSPyMongoRAG.Doc"]) -> str:
            """Numbered blocks: [1] (id=...) <title?>\\n<text>"""
            out = []
            for i, d in enumerate(docs, 1):
                title = d.meta.get("title") or d.meta.get("skill") or ""
                head = f"[{i}] (id={d.id}) {title}".strip()
                out.append(f"{head}\n{d.text}")
            return "\n\n".join(out)

    # ----------------------------
    # 2) LangChain VectorStore adapter
    # ----------------------------

    class _LCMongoRetriever(_SimpleFormatterMixin):
        """
        Thin adapter over LangChain's MongoDBAtlasVectorSearch.
        Enhanced with hybrid search (RRF + MMR) support.
        """
        def __init__(
            self,
            vector_store: MongoDBAtlasVectorSearch,
            *,
            title_key: str = "title",
            topic_key: str = "topic",
            grade_key: str = "grade",
            enable_hybrid: bool = False,
            mmr_lambda: float = 0.6,
        ):
            self.vs = vector_store
            self.title_key = title_key
            self.topic_key = topic_key
            self.grade_key = grade_key
            self.enable_hybrid = enable_hybrid
            self.mmr_lambda = mmr_lambda

        @cache_search
        def search(
            self,
            query: str,
            *,
            k: int = 8,
            filters: Optional[Dict[str, Any]] = None
        ) -> List["DSPyMongoRAG.Doc"]:
            # Newer LC supports pre_filter for Atlas; fallback if unavailable.
            try:
                # Retrieve 2x k for hybrid search diversity
                search_k = k * 2 if self.enable_hybrid else k
                docs = self.vs.similarity_search(query, k=search_k, pre_filter=(filters or {}))
            except TypeError:
                search_k = k * 2 if self.enable_hybrid else k
                docs = self.vs.similarity_search(query, k=search_k)

            # Convert to Doc format
            out: List[DSPyMongoRAG.Doc] = []
            for i, d in enumerate(docs):
                md = getattr(d, "metadata", {}) or {}
                out.append(DSPyMongoRAG.Doc(
                    id=str(md.get("_id") or md.get("id") or i),
                    text=(getattr(d, "page_content", "") or md.get("text", "")),
                    meta={
                        "title": md.get(self.title_key),
                        "topic": md.get(self.topic_key),
                        "grade": md.get(self.grade_key),
                    }
                ))

            # Apply MMR diversity if hybrid mode enabled
            if self.enable_hybrid and len(out) > k:
                try:
                    # Convert to ScoredDoc format
                    scored_docs = [
                        ScoredDoc(id=doc.id, text=doc.text, score=1.0/(i+1), meta=doc.meta)
                        for i, doc in enumerate(out)
                    ]

                    # Use hybrid search for diversity (MMR only, no BM25 fusion here)
                    diverse_docs = hybrid_search(
                        query=query,
                        vector_search_fn=lambda q, k: scored_docs[:k],
                        embed_fn=lambda t: self.vs._embedding.embed_query(t) if hasattr(self.vs, '_embedding') else None,
                        k_vector=len(scored_docs),
                        mmr_lambda=self.mmr_lambda,
                        final_k=k
                    )

                    # Convert back to Doc format (hybrid_search returns dicts)
                    out = [
                        DSPyMongoRAG.Doc(
                            id=d['id'],
                            text=d['text'],
                            meta=d.get('meta', {})
                        )
                        for d in diverse_docs
                    ]
                except Exception as e:
                    logger.warning(f"Hybrid search failed, falling back to basic: {e}")
                    out = out[:k]
            else:
                out = out[:k]

            return out

    # ----------------------------
    # 3) Stage specs (declarative)
    # ----------------------------

    @dataclass
    class RetrievalSpec:
        retriever: "DSPyMongoRAG.Retriever"
        k: int = 8
        filters: Union[Dict[str, Any], Callable[[BaseModel], Dict[str, Any]], None] = None
        rewrite: bool = True
        rewrite_instructions: Optional[str] = None
        # Where to read the query string from input model; fallback to entire input JSON
        query_field: Optional[str] = None

    @dataclass
    class StageSpec:
        name: str
        input_model: Type[BaseModel]
        output_model: Type[BaseModel]
        sys_instructions: str
        retrieval: Optional["DSPyMongoRAG.RetrievalSpec"] = None
        # Optional Critic→Revise
        critic_instructions: Optional[str] = "Identify unsupported claims, wrong facts, or missing citations."
        rounds: int = 1
        # Decoding
        temperature: float = 0.2
        max_tokens: int = 1024
        # Bypass LM & build deterministically (useful for retrieval packaging)
        deterministic: bool = False
        compute: Optional[Callable[[BaseModel], BaseModel]] = None

    # ----------------------------
    # 4) Built-in schemas
    # ----------------------------

    class RetrievalInput(BaseModel):
        question: str
        grade: Optional[int] = None
        topic_hint: Optional[str] = None

    class SelectedPassages(BaseModel):
        passages: str
        doc_ids: List[str] = Field(default_factory=list)

    class AnswerInput(BaseModel):
        passages: str
        question: str

    class FinalAnswer(BaseModel):
        answer: str
        citations: List[str] = Field(default_factory=list)
        confidence: float = 0.0

    # ----------------------------
    # 5) DSPy Signatures (typed)
    # ----------------------------

    class RewriteSig(dspy.Signature):
        """Produce a concise retrieval query from the input JSON and optional hints."""
        sys_instructions: str = dspy.InputField()
        input_json: str       = dspy.InputField()
        query: str            = dspy.OutputField()

    class UniversalSig(dspy.Signature):
        """
        Run a stage with:
        - sys_instructions: stage rules + JSON-only contract
        - input_json: Pydantic-confirmed input
        - passages: optional retrieved evidence (numbered [n])
        - result_json: JSON for the stage's output_model schema
        """
        sys_instructions: str = dspy.InputField()
        input_json: str       = dspy.InputField()
        passages: str         = dspy.InputField()
        result_json: str      = dspy.OutputField()

    class CriticSig(dspy.Signature):
        """List concrete issues with the candidate JSON vs. instructions/evidence/schema."""
        sys_instructions: str   = dspy.InputField()
        passages: str       = dspy.InputField()
        candidate_json: str = dspy.InputField()
        issues: str         = dspy.OutputField()

    class ReviseSig(dspy.Signature):
        """Fix issues; return ONLY valid JSON for the target schema."""
        sys_instructions: str   = dspy.InputField()
        passages: str       = dspy.InputField()
        candidate_json: str = dspy.InputField()
        issues: str         = dspy.InputField()
        result_json: str    = dspy.OutputField()

    # ----------------------------
    # 6) Init (no LM here)
    # ----------------------------

    _CITE_RE = re.compile(r"\[(\d+)\]")

    def __init__(
        self,
        *,
        # Either provide a ready vector_store, or the DB params to fetch one.
        vector_store: Optional[MongoDBAtlasVectorSearch] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None,
        text_key: Optional[str] = None,
        embedding_key: Optional[str] = None,
        # Optional metadata field names for title/topic/grade in Documents
        title_key: str = "title",
        topic_key: str = "topic",
        grade_key: str = "grade",
        # DSPy improvements
        enable_hybrid: bool = False,
        mmr_lambda: float = 0.6,
        provider: str = "falcon",
        # Robust JSON parser (str->obj)
    ):
        """
        Args:
            vector_store: a MongoDBAtlasVectorSearch (LangChain) instance.
            db_name, collection_name, index_name, text_key, embedding_key:
                If vector_store is None, these are passed to `get_vector_store(...)`.
            title_key, topic_key, grade_key:
                Document metadata keys to surface in passages.
            enable_hybrid: Enable hybrid retrieval (MMR diversity)
            mmr_lambda: MMR lambda parameter (0.6 = 60% relevance, 40% diversity)
            provider: LLM provider for token budgeting ('falcon' or 'openai')
        """
        self.parse_json = parse_json or (lambda s: json.loads(s))

        if vector_store is None:
            # Acquire via your singleton factory with parameters
            if not all([db_name, collection_name, index_name, text_key, embedding_key]):
                raise ValueError(
                    "Provide either `vector_store` or all of: db_name, collection_name, index_name, text_key, embedding_key."
                )
            # get_vector_store must accept these 5 parameters
            vector_store = get_vector_store(  # type: ignore[arg-type]
                db_name=db_name,
                coll_name=collection_name,
                index_name=index_name,
                text_key=text_key,
                embedding_key=embedding_key,
            )

        self.retriever: DSPyMongoRAG._LCMongoRetriever = DSPyMongoRAG._LCMongoRetriever(
            vector_store,
            title_key=title_key,
            topic_key=topic_key,
            grade_key=grade_key,
            enable_hybrid=enable_hybrid,
            mmr_lambda=mmr_lambda,
        )

        # Token budget for adaptive allocation
        self.token_budget: AdaptiveTokenBudget = get_budget(provider)

        # Keep last retrieval ids for citation mapping
        self._last_doc_ids: List[str] = []

        # Stage metrics for telemetry
        self.stage_metrics: List[Dict[str, Any]] = []

    # ----------------------------
    # 7) Utilities
    # ----------------------------

    @staticmethod
    def _strip_fences(s: str) -> str:
        t = (s or "").strip()
        if t.startswith("```"):
            t = t.strip("`")
            if "\n" in t:
                t = t.split("\n", 1)[1]
        if t.endswith("```"):
            t = t[:-3].strip()
        return t

    @staticmethod
    def _model_to_json(m: BaseModel) -> str:
        return m.model_dump_json(by_alias=True, exclude_none=True)

    def _parse_and_validate(self, jsonish: str, schema: Type[BaseModel]) -> Optional[BaseModel]:
        t = DSPyMongoRAG._strip_fences(jsonish)
        try:
            parsed = self.parse_json(t)  # external, robust parser
        except Exception:
            return None
        try:
            return schema.model_validate(parsed)
        except ValidationError:
            return None

    @staticmethod
    def _read_field(obj: BaseModel, dotted: Optional[str]) -> Optional[str]:
        if not dotted:
            return None
        cur: Any = obj.model_dump()
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur if isinstance(cur, str) else None

    @staticmethod
    def _sys_rules(extra: str) -> str:
        return (
            "Return ONLY valid JSON that matches the required schema exactly. "
            "Do not include explanations or code fences. "
            + (extra or "")
        )


    @staticmethod
    def _map_citations_to_ids(answer_text: str, ordered_ids: List[str]) -> List[str]:
        seen, citations = set(), []
        for m in DSPyMongoRAG._CITE_RE.finditer(answer_text or ""):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(ordered_ids):
                did = ordered_ids[idx]
                if did not in seen:
                    seen.add(did); citations.append(did)
        return citations

    # ----------------------------
    # 8) Stage factories (easy)
    # ----------------------------

    def stage_retrieve(
        self,
        *,
        retriever: Optional["DSPyMongoRAG.Retriever"] = None,
        k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
        query_field: str = "question",
        rewrite: bool = True,
        rewrite_instructions: Optional[str] = None,
        instructions: Optional[str] = None,
        max_tokens: int = 512,
        deterministic: bool = True,   # no LLM cost to format SelectedPassages
    ) -> "DSPyMongoRAG.StageSpec":
        """
        Retrieval stage:
        in  = RetrievalInput(question, grade?, topic_hint?)
        out = SelectedPassages(passages, doc_ids)
        """
        retr = retriever or self.retriever

        return DSPyMongoRAG.StageSpec(
            name="retrieve",
            input_model=DSPyMongoRAG.RetrievalInput,
            output_model=DSPyMongoRAG.SelectedPassages,
            sys_instructions= instructions or (
                "Package the retrieved text into a single numbered block string (passages). "
                "Keep numbering and ids stable as provided (e.g., [1] (id=...) ...). "
                "If nothing is found, return empty passages and an empty doc_ids list."
            ),
            retrieval=DSPyMongoRAG.RetrievalSpec(
                retriever=retr, k=k, filters=filters or {},
                rewrite=rewrite, rewrite_instructions=rewrite_instructions,
                query_field=query_field
            ),
            rounds=0,
            max_tokens=max_tokens,
            temperature=0.0,
            deterministic=deterministic,
        )

    def stage_answer(
        self,
        *,
        instructions: Optional[str] = None,
        critic_instructions: Optional[str] = "Point out any claims not supported by the passages or missing citations.",
        rounds: int = 1,
        max_tokens: int = 768,
        temperature: float = 0.2,
    ) -> "DSPyMongoRAG.StageSpec":
        """
        Answer stage:
        in  = AnswerInput(passages, question)
        out = FinalAnswer(answer, citations[], confidence)
        """
        return DSPyMongoRAG.StageSpec(
            name="answer",
            input_model=DSPyMongoRAG.AnswerInput,
            output_model=DSPyMongoRAG.FinalAnswer,
            sys_instructions= instructions or (
                "Answer using ONLY the passages. "
                "Cite sources inline like [1],[2] and set 'citations' to the referenced doc ids. "
                "If unsure, return 'insufficient evidence'. "
                "Set confidence higher when multiple passages support the same claim."
            ),
            retrieval=None,
            critic_instructions=critic_instructions,
            rounds=rounds,
            max_tokens=max_tokens,
            temperature=temperature
        )

    # ----------------------------
    # 9) Runner (N stages)
    # ----------------------------

    @cache_rewrite
    def _cached_rewrite(self, sys_instr: str, raw_query: str) -> str:
        """Cached query rewriting"""
        with dspy.context(lm=lm):
            Rewrite = dspy.Predict(DSPyMongoRAG.RewriteSig)
            result = Rewrite(
                sys_instructions=sys_instr,
                input_json=str(raw_query),
                max_tokens=96,
                temperature=0.0
            ).query
            return result or str(raw_query)

    @timeout(180)  # 3 minutes timeout
    def run(self, *, stages: List["DSPyMongoRAG.StageSpec"], initial_input: BaseModel, _retry_count: int = 0) -> BaseModel:
        """
        Execute N stages with the provided LM. Returns the final stage's Pydantic object.
        Implements context window retry logic to handle token limit exceeded errors.
        Times out after 3 minutes to prevent hanging.
        Enhanced with token budgeting and telemetry.
        """
        try:
            cur_obj: BaseModel = initial_input
            self._last_doc_ids = []
            self.stage_metrics = []

            # Check overflow risk before starting
            stage_names = [s.name for s in stages]
            stage_inputs = {s.name: DSPyMongoRAG._model_to_json(initial_input) for s in stages}

            if self.token_budget.check_overflow_risk(stage_names, stage_inputs):
                logger.warning("⚠️ Context overflow risk detected, pipeline may need splitting")

            with dspy.context(lm=lm):
                # Instantiate DSPy modules inside the same thread/context
                Execute = dspy.ChainOfThought(DSPyMongoRAG.UniversalSig)
                Critic  = dspy.Predict(DSPyMongoRAG.CriticSig)
                Revise  = dspy.Predict(DSPyMongoRAG.ReviseSig)

                for stage in stages:
                    stage_start = time.time()
                    # 1) Validate input shape
                    if not isinstance(cur_obj, stage.input_model):
                        raise TypeError(f"Stage '{stage.name}': input is not {stage.input_model.__name__}")

                    # COMPUTE-ONLY STAGE (pure Python function)
                    if stage.compute is not None:
                        out_obj = stage.compute(cur_obj)
                        if not isinstance(out_obj, stage.output_model):
                            raise TypeError(f"Stage '{stage.name}': compute() must return {stage.output_model.__name__}")
                        cur_obj = out_obj
                        continue

                    input_json = DSPyMongoRAG._model_to_json(cur_obj)
                    passages = ""

                    # 2) Retrieval
                    hits: List[DSPyMongoRAG.Doc] = []

                    if stage.retrieval is not None:
                        r = stage.retrieval
                        raw_query = DSPyMongoRAG._read_field(cur_obj, r.query_field) if r.query_field else input_json
                        query = raw_query
                        if r.rewrite:
                            sys_instr = r.rewrite_instructions or "Rewrite into a short, retrieval-friendly query capturing key entities and constraints."
                            # Use cached rewrite
                            query = self._cached_rewrite(sys_instr, str(raw_query))

                        # Resolve filters at execution time
                        if callable(r.filters):
                            resolved_filters = r.filters(cur_obj)
                        else:
                            resolved_filters = r.filters or {}

                        hits = r.retriever.search(query, k=r.k, filters=resolved_filters)
                        passages = "" if not hits else r.retriever.format_passages(hits)
                        self._last_doc_ids = [d.id for d in hits]

                    # 3) Deterministic packaging for retrieval
                    if stage.deterministic and stage.output_model is DSPyMongoRAG.SelectedPassages:
                        out_obj = DSPyMongoRAG.SelectedPassages(passages=passages, doc_ids=self._last_doc_ids.copy())
                        cur_obj = out_obj
                        continue

                    # 4) Execute via DSPy with token budgeting
                    sys_text = DSPyMongoRAG._sys_rules(stage.sys_instructions)

                    # Allocate tokens adaptively
                    allocation = self.token_budget.allocate(
                        stage=stage.name,
                        input_text=input_json + passages
                    )

                    candidate = Execute(
                        sys_instructions=sys_text,
                        input_json=input_json,
                        passages=passages,
                        max_tokens=min(stage.max_tokens, allocation.allocated_tokens),
                        temperature=stage.temperature
                    ).result_json

                    # Record metrics
                    self.stage_metrics.append({
                        'stage': stage.name,
                        'latency_ms': int((time.time() - stage_start) * 1000),
                        'tokens_allocated': allocation.allocated_tokens,
                        'tokens_utilization': allocation.utilization,
                        'success': True
                    })

                    out_obj = self._parse_and_validate(candidate, stage.output_model)

                    # Partial-output repair: if model types match, merge candidate onto input
                    if out_obj is None and (stage.output_model is stage.input_model):
                        try:
                            raw = self.parse_json(DSPyMongoRAG._strip_fences(candidate))
                        except Exception:
                            raw = None
                        if isinstance(raw, dict):
                            try:
                                base = cur_obj.model_dump()
                                merged = {**base, **raw}
                                out_obj = stage.output_model.model_validate(merged)
                            except Exception:
                                out_obj = None

                    # 5) Critic→Revise
                    if out_obj is None and stage.critic_instructions:
                        issues = Critic(
                            sys_instructions=stage.critic_instructions,
                            passages=passages,
                            candidate_json=candidate,
                            max_tokens=256,
                            temperature=0.0
                        ).issues

                        for _ in range(max(1, stage.rounds)):
                            candidate = Revise(
                                sys_instructions=stage.critic_instructions,
                                passages=passages,
                                candidate_json=candidate,
                                issues=issues,
                                max_tokens=stage.max_tokens,
                                temperature=stage.temperature
                            ).result_json
                            out_obj = self._parse_and_validate(candidate, stage.output_model)
                            if out_obj is not None:
                                break

                    if out_obj is None:
                        raise ValueError(f"Stage '{stage.name}' failed to produce valid {stage.output_model.__name__} JSON.")

                    # 6) Post-processing for FinalAnswer: map [n] → doc_ids if missing
                    if isinstance(out_obj, DSPyMongoRAG.FinalAnswer) and (not out_obj.citations):
                        out_obj.citations = DSPyMongoRAG._map_citations_to_ids(out_obj.answer, self._last_doc_ids)

                    cur_obj = out_obj

            return cur_obj

        except Exception as ex:
            # Check if this is a context window exceeded error and we haven't retried yet
            error_str = str(ex).lower()
            is_context_error = any(keyword in error_str for keyword in [
                'context window', 'context length', 'maximum context', 'token limit', 'contextwindowexceedederror'
            ])

            if is_context_error and _retry_count == 0:
                # Split stages into two groups for sequential execution
                mid_point = len(stages) // 2
                first_batch = stages[:mid_point] if mid_point > 0 else stages[:1]
                second_batch = stages[mid_point:] if mid_point < len(stages) else []

                # Run first batch
                first_result = self.run(stages=first_batch, initial_input=initial_input, _retry_count=1)

                if not second_batch:
                    # If no second batch, return first result
                    return first_result

                # Run second batch using first batch result as input
                # Adapt the input for the second batch's expected input model
                second_input = self._adapt_input_for_second_batch(first_result, second_batch[0].input_model)
                second_result = self.run(stages=second_batch, initial_input=second_input, _retry_count=1)

                # Combine results from both batches
                return self._combine_batch_results(first_result, second_result)

            return DSPyMongoRAG.FinalAnswer(
                answer=f"Error: {str(ex)}",
                citations=[],
                confidence=0.0
            )

    def _adapt_input_for_second_batch(self, first_result: BaseModel, expected_input_model) -> BaseModel:
        """
        Adapt the result from the first batch to serve as input for the second batch.
        """
        # If the first result already matches the expected input model, check if truncation needed
        if isinstance(first_result, expected_input_model):
            # If it's SelectedPassages and potentially too large, truncate it
            if isinstance(first_result, DSPyMongoRAG.SelectedPassages):
                if len(first_result.passages) > 3000:
                    return DSPyMongoRAG.SelectedPassages(
                        passages=first_result.passages[:3000],
                        doc_ids=first_result.doc_ids
                    )
            return first_result

        # Handle common adaptations
        if expected_input_model is DSPyMongoRAG.SelectedPassages:
            # Convert FinalAnswer to SelectedPassages for curation stage
            if isinstance(first_result, DSPyMongoRAG.FinalAnswer):
                # Truncate passages to prevent context overflow in second batch
                truncated_passages = first_result.answer[:3000] if first_result.answer else ""
                return DSPyMongoRAG.SelectedPassages(
                    passages=truncated_passages,
                    doc_ids=first_result.citations or self._last_doc_ids
                )
            # Convert RetrievalInput to SelectedPassages
            elif hasattr(first_result, 'question'):
                truncated_content = getattr(first_result, 'question', '')[:3000]
                return DSPyMongoRAG.SelectedPassages(
                    passages=truncated_content,
                    doc_ids=self._last_doc_ids
                )

        elif expected_input_model is DSPyMongoRAG.FinalAnswer:
            # Convert other types to FinalAnswer
            if isinstance(first_result, DSPyMongoRAG.SelectedPassages):
                return DSPyMongoRAG.FinalAnswer(
                    answer=first_result.passages,
                    citations=first_result.doc_ids,
                    confidence=0.8
                )
            elif hasattr(first_result, 'question'):
                return DSPyMongoRAG.FinalAnswer(
                    answer=getattr(first_result, 'question', ''),
                    citations=self._last_doc_ids,
                    confidence=0.8
                )

        elif expected_input_model is DSPyMongoRAG.RetrievalInput:
            # Convert to RetrievalInput
            if isinstance(first_result, DSPyMongoRAG.FinalAnswer):
                return DSPyMongoRAG.RetrievalInput(
                    question=first_result.answer[:500],  # Truncate to manageable size
                    grade=getattr(first_result, 'grade', None)
                )
            elif isinstance(first_result, DSPyMongoRAG.SelectedPassages):
                return DSPyMongoRAG.RetrievalInput(
                    question=first_result.passages[:500],  # Truncate to manageable size
                    grade=None
                )

        # Fallback: try to extract text content and create RetrievalInput
        text_content = ""
        if hasattr(first_result, 'answer'):
            text_content = first_result.answer
        elif hasattr(first_result, 'passages'):
            text_content = first_result.passages
        elif hasattr(first_result, 'question'):
            text_content = first_result.question
        else:
            text_content = str(first_result)

        # Default fallback to RetrievalInput
        return DSPyMongoRAG.RetrievalInput(
            question=text_content[:500],  # Truncate to manageable size
            grade=getattr(first_result, 'grade', None)
        )

    def _combine_batch_results(self, first_result: BaseModel, second_result: BaseModel) -> BaseModel:
        """
        Combine results from two batch runs into a final result.
        Generally, the second result should be the final output, but we may want to preserve
        some information from the first result.
        """
        # If second result is FinalAnswer, enhance it with first result data
        if isinstance(second_result, DSPyMongoRAG.FinalAnswer):
            # Combine citations from both results
            combined_citations = []
            if isinstance(first_result, DSPyMongoRAG.FinalAnswer) and first_result.citations:
                combined_citations.extend(first_result.citations)
            if second_result.citations:
                combined_citations.extend(second_result.citations)

            # Remove duplicates while preserving order
            seen = set()
            unique_citations = []
            for citation in combined_citations:
                if citation not in seen:
                    seen.add(citation)
                    unique_citations.append(citation)

            return DSPyMongoRAG.FinalAnswer(
                answer=second_result.answer,
                citations=unique_citations,
                confidence=max(second_result.confidence,
                             getattr(first_result, 'confidence', 0.0) if hasattr(first_result, 'confidence') else 0.0)
            )

        # If second result is SelectedPassages, convert to FinalAnswer
        elif isinstance(second_result, DSPyMongoRAG.SelectedPassages):
            return DSPyMongoRAG.FinalAnswer(
                answer=second_result.passages,
                citations=second_result.doc_ids,
                confidence=0.8
            )

        # Default: return second result as it represents the final stage
        return second_result

    # ----------------------------
    # 10) Easiest helpers
    # ----------------------------

    def run_easy(
        self,
        *,
        question: str,
        grade: Optional[int] = None,
        stages: List["DSPyMongoRAG.StageSpec"],
    ) -> BaseModel:
        """
        Auto-create the first input and run the provided stages with lm.
        """
        initial = DSPyMongoRAG.RetrievalInput(question=question, grade=grade)
        return self.run(stages=stages, initial_input=initial)

    def easy_answer(
        self,
        *,
        question: str,
        grade: Optional[int] = None,
        k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        One-call: retrieve + answer using built-ins. Returns dict(FinalAnswer).
        """
        stages = [
            self.stage_retrieve(k=k, filters=filters or {}),
            self.stage_answer(rounds=1),
        ]
        final = self.run_easy(question=question, grade=grade, stages=stages)
        if isinstance(final, DSPyMongoRAG.FinalAnswer):
            return final.model_dump()
        # In case caller supplied a custom last stage, coerce best-effort:
        try:
            coerced = DSPyMongoRAG.FinalAnswer.model_validate(final.model_dump())
            return coerced.model_dump()
        except Exception:
            return {"answer": "insufficient evidence", "citations": [], "confidence": 0.0}
