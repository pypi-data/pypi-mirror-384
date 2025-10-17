"""
Centralized LLM Management System - Multi-Provider Support
"""

import logging
import os
import json
import dspy
import requests
import time
import asyncio
from typing import Dict, Any, Optional, List, Type
from functools import wraps

from openai import OpenAI
from langchain_openai import ChatOpenAI
from contextlib import contextmanager
from pydantic import BaseModel
from google import genai

# Import the comprehensive JSON repair function from dedicated module
from src.utils.json_repair import parse_json
from src.config import Config

logger = logging.getLogger(__name__)

# ==========================================
# Rate Limiting & Load Balancing
# ==========================================

class RateLimiter:
    """Simple token bucket rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.lock = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.lock = asyncio.Lock()
        except RuntimeError:
            pass  # No event loop, sync mode only

    async def acquire_async(self):
        """Async version of acquire for async contexts."""
        if self.lock:
            async with self.lock:
                self._refill()
                while self.tokens < 1:
                    await asyncio.sleep(0.1)
                    self._refill()
                self.tokens -= 1
        else:
            self.acquire()

    def acquire(self):
        """Acquire a token, blocking if necessary."""
        self._refill()
        while self.tokens < 1:
            time.sleep(0.1)
            self._refill()
        self.tokens -= 1

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.requests_per_minute,
            self.tokens + elapsed * (self.requests_per_minute / 60.0)
        )
        self.last_update = now

# Global rate limiters per provider
_rate_limiters = {
    'openai': RateLimiter(requests_per_minute=500),  # OpenAI tier limits
    'falcon': RateLimiter(requests_per_minute=100),
    'k2': RateLimiter(requests_per_minute=100),
    'dspy': RateLimiter(requests_per_minute=1200),  # Increased to 1200 (20 req/sec)
}

def with_retry_and_rate_limit(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to add retry logic and rate limiting to LLM calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            provider = kwargs.get('provider', 'openai')
            rate_limiter = _rate_limiters.get(provider)

            for attempt in range(max_retries):
                try:
                    # Acquire rate limit token
                    if rate_limiter:
                        rate_limiter.acquire()

                    return func(*args, **kwargs)

                except Exception as e:
                    error_str = str(e).lower()
                    error_type = type(e).__name__.lower()

                    # Check if it's a rate limit error
                    is_rate_limit = any(x in error_str for x in [
                        'rate limit', 'too many requests', '429', 'quota'
                    ])

                    # Check if it's a retriable error (including timeouts)
                    is_retriable = is_rate_limit or any(x in error_str or x in error_type for x in [
                        'timeout', 'timed out', 'connection', 'server error', '500', '502', '503', '504',
                        'readtimeout', 'apitimeouterror'
                    ])

                    if attempt < max_retries - 1 and is_retriable:
                        # Use longer backoff for timeouts
                        if 'timeout' in error_str or 'timeout' in error_type:
                            wait_time = (backoff_factor ** attempt) * 3  # 6s, 12s, 24s for timeouts
                        else:
                            wait_time = backoff_factor ** attempt

                        logger.warning(
                            f"⏳ {provider.upper()} request failed (attempt {attempt + 1}/{max_retries}): {type(e).__name__}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        raise

            raise RuntimeError(f"Max retries ({max_retries}) exceeded")
        return wrapper
    return decorator

# ==========================================
# Provider Selection Configuration
# ==========================================

# Environment variable to choose provider globally: 'openai' or 'falcon'
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

logger.info(f"LLM Provider configured: {DEFAULT_PROVIDER}")

# ==========================================
# OpenAI LLM Configuration (Original)
# ==========================================

_llm_gpt5 = ChatOpenAI(
    model="gpt-5",
    api_key=Config.OPENAI_API_KEY,
)

openai_client = OpenAI(api_key=Config.OPENAI_API_KEY, timeout=300.0)  # Increased to 5 minutes for scaffolding

# ==========================================
# Falcon Configuration (HTTP API + HF Endpoint fallback)
# ==========================================


def get_falcon_api_base_url():
    """Get Falcon API base URL from environment, allowing for dynamic updates."""
    return os.getenv("FALCON_API_BASE_URL")


def get_openai_api_base_url():
    """Get OpenAI API base URL from environment, allowing for dynamic updates."""
    return os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")


FALCON_API_BASE_URL = get_falcon_api_base_url()  # Falcon HTTP API endpoint
OPENAI_API_BASE_URL = get_openai_api_base_url()  # OpenAI API endpoint

# dspy_lm = dspy.LM(
#     "openai/tiiuae/Falcon-H1-7B-Instruct",
#     api_base="https://eddfd2bu9axwzgho.us-east-1.aws.endpoints.huggingface.cloud/v1",
#     api_key=Config.HF_API_TOKEN,
#     model_type="chat",
#     max_tokens=3500,
#     timeout=180
# )
dspy_lm = dspy.LM(
    "openai/tiiuae/Falcon-H1-34B-Instruct",
    api_base=FALCON_API_BASE_URL,
    api_key="",
    model_type="chat",
    max_tokens=1500,
    timeout=180,
    temperature=0.4,
    cache=False  # Disable cache
)
dspy.configure(lm=dspy_lm)


def limit_tokens(messages: List[Dict[str, str]], requested_tokens: int, provider: str = 'openai') -> int:
    """Calculate safe max_tokens to ensure input + output doesn't exceed model's context window"""
    # Token estimate: ~4 chars per token for English, ~2.5 for Arabic (more conservative)
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    # Detect if content is primarily Arabic (contains Arabic characters)
    has_arabic = any('\u0600' <= c <= '\u06FF' for msg in messages for c in msg.get("content", ""))
    estimated_input_tokens = int(total_chars / 2.5) if has_arabic else int(total_chars / 4)

    # Set maximum context window per provider
    if provider == 'k2':
        MAXIMUM_TOKENS = 32000
    elif provider == 'falcon':
        MAXIMUM_TOKENS = 7850
    elif provider == 'dspy':
        MAXIMUM_TOKENS = 5192
    elif provider == 'openai':
        MAXIMUM_TOKENS = 16000
    else:
        MAXIMUM_TOKENS = 6000

    # Add safety buffer (15% of context window or 512 tokens, whichever is smaller)
    # This accounts for tokenizer overhead, system messages, and formatting
    safety_buffer = min(int(MAXIMUM_TOKENS * 0.15), 512)
    available_output_tokens = MAXIMUM_TOKENS - estimated_input_tokens - safety_buffer

    # Return the smaller of requested max_tokens or what's safe, with minimum of 100
    return max(min(requested_tokens, available_output_tokens), 100)


def solve_with_dspy(
    messages: List[Dict[str, str]],
    max_tokens: int = 8000,
    *,
    temperature: float = 0.0,
    timeout: int = 1800,
    do_not_parse_json: bool = False,
) -> Any:
    """
    Solve function specifically for DSPy provider.

    Args:
        messages: Chat messages in OpenAI format.
        max_tokens: Max tokens for output.
        temperature: Decoding temperature.
        timeout: Request timeout.
    """
# --- read system/user messages (your contract says there are exactly two) ---
    system_msg = next((m["content"] for m in messages if m.get("role") == "system"), "")
    user_msg   = next((m["content"] for m in messages if m.get("role") == "user"), "")
    if not system_msg or not user_msg:
        raise ValueError("DSPy provider expects exactly one system and one user message.")

    # --- accurate token budgeting against the real model id ---
    safe_tokens = int(limit_tokens(messages, max_tokens, 'dspy'))

    # --- detect JSON-only and common constraints from the instructions ---
    sys_low = system_msg.lower()
    user_low = user_msg.lower()
    # Detect JSON strictly if either message strongly requires it
    wants_json = (
        ("json" in sys_low and any(x in sys_low for x in ["only", "valid", "schema", "output"]))
        or ("json" in user_low and any(x in user_low for x in ["only", "valid", "schema", "output"]))
    )
    wants_one_line  = "one sentence" in sys_low or "single sentence" in sys_low or "single line" in sys_low
    # Respect explicit no-CoT instructions
    wants_no_cot    = (
        "do not reveal" in sys_low or "no chain-of-thought" in sys_low or "no reasoning" in sys_low
        or "do not reveal" in user_low or "no chain-of-thought" in user_low or "no reasoning" in user_low
    )

    # local DSPy context (no global configure; thread-safe)
    @contextmanager
    def _ctx():
        with dspy.context(lm=dspy_lm):
            yield

    # ----- Signatures -----
    class DraftSig(dspy.Signature):
        """
        Produce the best possible answer STRICTLY following the instructions.
        Think step-by-step privately. DO NOT reveal your chain-of-thought.
        If JSON is requested, return ONLY valid JSON (no prose, no fences).
        """
        sys_instructions  = dspy.InputField()
        task          = dspy.InputField()
        target_format = dspy.InputField(desc="Either 'json' or 'text'.")
        candidate     = dspy.OutputField()

    class CriticSig(dspy.Signature):
        """
        Review the candidate against the instructions.
        Flag ANY violations: wrong format, extra text, missing fields, empty values,
        math errors, unverifiable claims (if instructions require verification),
        'one sentence' constraint, etc. Say 'no issues' if perfect.
        """
        sys_instructions = dspy.InputField()
        task         = dspy.InputField()
        target_format= dspy.InputField()
        candidate    = dspy.InputField()
        issues       = dspy.OutputField()

    class ReviseSig(dspy.Signature):
        """
        Fix the candidate so it FULLY satisfies the instructions and format.
        Return ONLY the final output (no explanations).
        """
        sys_instructions = dspy.InputField()
        task         = dspy.InputField()
        target_format= dspy.InputField()
        candidate    = dspy.InputField()
        issues       = dspy.InputField()
        final        = dspy.OutputField()

    # Switch to non-CoT when explicitly requested to reduce spillover
    Draft  = dspy.Predict(DraftSig) if wants_no_cot else dspy.ChainOfThought(DraftSig)
    Critic = dspy.Predict(CriticSig)         # sharp check
    Revise = dspy.Predict(ReviseSig)         # constrained rewrite

    target_format = "json" if wants_json else "text"

    # Helper to detect infinite reasoning loops
    def _has_repetitive_pattern(text: str, min_repeat: int = 3) -> bool:
        """Detect if text has repetitive phrases (sign of infinite loop)"""
        text_str = str(text)
        if len(text_str) < 100:
            return False
        # Check for repeated phrases (10+ chars) appearing 3+ times
        words = text_str.split()
        for i in range(len(words) - 5):
            phrase = " ".join(words[i:i+5])  # 5-word phrases
            if len(phrase) >= 10 and text_str.count(phrase) >= min_repeat:
                return True
        return False

    with _ctx():
        # 1) Draft
        cand = Draft(
            sys_instructions=system_msg,
            task=user_msg,
            target_format=target_format,
            max_tokens=safe_tokens,
            temperature=float(temperature),
        ).candidate

        # Early exit if repetitive loop detected
        if _has_repetitive_pattern(cand):
            logger.warning("DSPy infinite loop detected in draft, using fallback")
            raise ValueError("Repetitive reasoning pattern detected - infinite loop")

        # 2) Critique
        issues = Critic(
            sys_instructions=system_msg,
            task=user_msg,
            target_format=target_format,
            candidate=cand,
            max_tokens=min(512, max(128, safe_tokens // 4)),
            temperature=0.0,  # keep the critic deterministic
        ).issues

        # 3) If needed, Revise once (you can loop if you like; 1 pass is usually enough)
        if issues.strip().lower() not in {"no issues", "none", "ok"}:
            cand = Revise(
                sys_instructions=system_msg,
                task=user_msg,
                target_format=target_format,
                candidate=cand,
                issues=issues + ("\nReturn ONLY the final output." if not wants_json else "\nReturn ONLY valid JSON."),
                max_tokens=safe_tokens,
                temperature=float(temperature),
            ).final

        # --- Hard post-guards based on instructions ---
        if wants_one_line:
            # collapse to one sentence/line without changing content meaningfully
            cand = " ".join(str(cand).split()).strip()

        # --- Return according to your existing API contract ---
        if do_not_parse_json or not wants_json:
            return cand

        # Helper to strip common Markdown code fences before parsing
        def _strip_fences(text: str) -> str:
            t = str(text).strip()
            if t.startswith("```"):
                t = t.strip("`\n ")
                # remove a leading language tag if present
                if "\n" in t:
                    t = t.split("\n", 1)[1]
            if t.endswith("```"):
                t = t[:-3].rstrip()
            return t

        # First parse attempt
        try:
            return parse_json(_strip_fences(cand))
        except Exception:
            pass

        # One more Critic→Revise pass before falling back
        try:
            issues2 = Critic(
                sys_instructions=system_msg,
                task=user_msg,
                target_format=target_format,
                candidate=cand,
                max_tokens=min(512, max(128, safe_tokens // 4)),
                temperature=0.0,
            ).issues
            cand2 = Revise(
                sys_instructions=system_msg,
                task=user_msg,
                target_format=target_format,
                candidate=cand,
                issues=issues2 + ("\nReturn ONLY valid JSON."),
                max_tokens=safe_tokens,
                temperature=float(temperature),
            ).final
            return parse_json(_strip_fences(cand2))
        except Exception:
            # last-chance repair
            class JsonFixSig(dspy.Signature):
                """Rewrite the text as ONLY a valid JSON object. No prose, no code fences."""
                text  = dspy.InputField()
                fixed = dspy.OutputField()

            Fix = dspy.Predict(JsonFixSig)
            fixed = Fix(text=cand, max_tokens=min(512, max(128, safe_tokens // 4)), temperature=0.0).fixed
            return parse_json(_strip_fences(fixed))


@with_retry_and_rate_limit(max_retries=3, backoff_factor=2.0)
def solve_with_llm(
    messages: List[Dict[str, str]],
    max_tokens: int = 8000,
    *,
    provider: str = "falcon",  # options: "falcon" or "k2" or "dspy"
    model: str = None,
    base_url: str = None,
    temperature: float = 0.0,
    timeout: int = 1800,
    do_not_parse_json: bool = False,
) -> Any:
    """
    Centralized solve function to handle both Falcon and K2 providers.

    Args:
        messages: Chat messages in OpenAI format.
        max_tokens: Max tokens for output.
        provider: "falcon" or "k2" (or "openai" for fallback).
        model: Override default model per provider.
        base_url: API base URL.
        temperature: Decoding temperature.
        timeout: Request timeout.
    """
    try:
        safe_max_tokens = limit_tokens(messages, max_tokens, provider)

        # Defaults per provider
        if provider == "k2":
            model = model or "LLM360/K2-Think"
            base_url = base_url or FALCON_API_BASE_URL
            url = f"{base_url}/chat/completions"
            payload = {
                "model": model,
                # enforce JSON-only output
                "response_format": {"type": "json_object"},
                "temperature": float(temperature),
                "max_tokens": int(safe_max_tokens),
                "messages": messages,
                "stop": ["</think>"],
            }

        elif provider == "falcon":
            model = model or "tiiuae/Falcon-H1-34B-Instruct"
            base_url = base_url or FALCON_API_BASE_URL
            url = f"{base_url}/chat/completions"
            payload = {
                "model": model,
                "temperature": float(temperature),
                "max_tokens": int(safe_max_tokens),
                "messages": messages,
            }
        
        elif provider == "dspy":
            # safe_tokens = int(limit_tokens(messages, max_tokens, provider=provider))
            # content = dspy_lm(messages=messages, max_tokens=safe_tokens)[0]

            # if do_not_parse_json:
            #     return content

            # return parse_json(content)
            return solve_with_dspy(
                messages,
                max_tokens,
                temperature=temperature,
                timeout=timeout,
                do_not_parse_json=do_not_parse_json,
            )

        else:
            resp = openai_client.responses.create(
                model='gpt-5',
                input=messages,
                max_output_tokens=limit_tokens(messages, max_tokens, 'openai')
            )
            if do_not_parse_json:
                return resp.output_text

            response = parse_json(resp.output_text)

            return response

        # Make request
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        if do_not_parse_json:
            return content

        return parse_json(content)

    except Exception as e:
        logger.error(f"Solve function error ({provider}): {e}")
        if model != "openai":
            logger.info("Falling back to OpenAI for this request")
            resp = openai_client.responses.create(
                model='gpt-5',
                input=messages,
                max_output_tokens=limit_tokens(messages, max_tokens, 'openai'),
            )
            response = parse_json(resp.output_text)

            return response
        raise e

# ==========================================
# Generic LLM Utility Functions (Multi-Provider)
# ==========================================

def produce_structured_response(
    messages: List[Dict[str, str]],
    structure_model: Type[BaseModel],
    model: Optional[str] = None,
    instructions: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = 2048,
    provider: Optional[str] = None,
) -> Any:
    """
    Produce a structured response using the configured provider.
    """
    effective_provider = (provider or DEFAULT_PROVIDER).lower()

    if effective_provider == "falcon":
        return _produce_structured_response_falcon(
            messages, structure_model, instructions, max_output_tokens
        )
    elif effective_provider == "dspy":
        return _produce_structured_response_dspy(
            messages, structure_model, max_output_tokens=max_output_tokens,
        )
    else:
        return _produce_structured_response_openai(
            messages, structure_model, "gpt-4o",
            instructions, temperature, max_output_tokens
        )


@with_retry_and_rate_limit(max_retries=3, backoff_factor=2.0)
def _produce_structured_response_openai(
    messages: List[Dict[str, str]],
    structure_model: Type[BaseModel],
    model: str,
    instructions: Optional[str],
    temperature: float,
    max_output_tokens: Optional[int],
    provider: str = "openai",  # Add provider parameter for decorator
) -> Any:
    """OpenAI structured response implementation."""
    # Convert to OpenAI message format
    formatted_messages = [
        {"role": m["role"], "content": m["content"]} for m in messages]

    # Add system instructions if provided
    if instructions:
        formatted_messages.insert(
            0, {"role": "system", "content": instructions})

    api_params: Dict[str, Any] = {
        "model": model,
        "messages": formatted_messages,
        "temperature": temperature,
        "response_format": structure_model,  # OpenAI Structured Outputs
    }
    if max_output_tokens:
        api_params["max_tokens"] = limit_tokens(
            formatted_messages, max_output_tokens, 'openai')

    try:
        response = openai_client.beta.chat.completions.parse(**api_params)
        if response.choices and response.choices[0].message.parsed:
            logger.debug(
                f"Structured response generated (OpenAI): {structure_model.__name__}")
            return response.choices[0].message.parsed
        raise RuntimeError("No parsed output in response")
    except Exception as e:
        logger.error(f"OpenAI structured response generation failed: {e}")
        raise


produce_structured_response_openai = _produce_structured_response_openai


def _produce_structured_response_falcon(
    messages: List[Dict[str, str]],
    structure_model: Type[BaseModel],
    instructions: Optional[str],
    max_output_tokens: Optional[int] = 25000,
) -> Any:
    """
    Falcon/DSPy structured response implementation.
    """
    try:
        # Build prompt with strict JSON schema instruction
        prompt_parts: List[str] = []
        if instructions:
            prompt_parts.append(f"System: {instructions}")

        for msg in messages:
            role = msg["role"].title()
            content = msg["content"]
            prompt_parts.append(f"{role}: {content}")

        schema = structure_model.model_json_schema()
        json_instruction = (
            "\n\n\n"
            + json.dumps(schema, indent=2)
            + "\n\nJSON Response:"
        )
        prompt = "\n\n".join(prompt_parts) + json_instruction

        messages = [
            {
                "role": "system",
                "content": "Assistant: Respond with ONLY valid JSON matching this schema exactly:",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        resp = solve_with_llm(messages, max_output_tokens, provider='falcon')

        # Minimal validation + single retry if schema not satisfied
        try:
            _payload = json.loads(resp) if isinstance(resp, str) else resp
            structure_model.model_validate(_payload)
        except Exception:
            resp = solve_with_llm(messages, max_output_tokens + 5000) # OpenAI fallback

        return resp

    except Exception as e:
        logger.error(f"Falcon structured response generation failed: {e}")
        raise


def _produce_structured_response_dspy(
    messages: List[Dict[str, str]],
    structure_model: Type[BaseModel],
    *,
    max_output_tokens: int = 2048,
    temperature: float = 0.2,
    retries: int = 2,
) -> Any:
    """
    Produce an EXACT structured response using DSPy with hidden reasoning (CoT),
    a critic pass, and a revise pass until the output validates against the
    provided Pydantic model schema. Returns a Python dict matching the schema.

    `messages` must contain one system and one user message.
    """
    # ---- extract the two messages ----
    system_msg = next((m["content"] for m in messages if m.get("role") == "system"), "")
    user_msg   = next((m["content"] for m in messages if m.get("role") == "user"), "")
    if not system_msg or not user_msg:
        raise ValueError("produce_structured_response_dspy expects exactly one system and one user message.")

    schema_json = json.dumps(structure_model.model_json_schema(), separators=(",", ":"))

    # ---- typed Signatures (IMPORTANT) ----
    class DraftSig(dspy.Signature):
        """
        Draft a complete JSON object matching the schema exactly.
        Think step-by-step privately. DO NOT reveal your chain-of-thought.
        Return ONLY valid JSON (no prose, no code fences).
        """
        sys_instructions: str = dspy.InputField(desc="System instructions to follow strictly.")
        task: str         = dspy.InputField(desc="User request or content to transform/answer.")
        json_schema: str  = dspy.InputField(desc="JSON Schema the output MUST satisfy.")
        json_out: str     = dspy.OutputField(desc="A single JSON object conforming to the schema.")


    class CriticSig(dspy.Signature):
        """
        Review the candidate JSON against the schema and instructions.
        List SPECIFIC issues: missing fields, wrong types, empty values,
        constraint mismatches, formatting errors. Say 'no issues' if perfect.
        """
        sys_instructions: str = dspy.InputField()
        task: str         = dspy.InputField()
        json_schema: str       = dspy.InputField()
        candidate: str    = dspy.InputField()
        issues: str       = dspy.OutputField()

    class ReviseSig(dspy.Signature):
        """
        Fix the candidate JSON so it FULLY satisfies the schema and instructions.
        Return ONLY valid JSON (no prose). Fill every required field non-empty.
        """
        sys_instructions: str = dspy.InputField()
        task: str         = dspy.InputField()
        json_schema: str       = dspy.InputField()
        candidate: str    = dspy.InputField()
        issues: str       = dspy.InputField()
        json_out: str     = dspy.OutputField()

    Draft  = dspy.ChainOfThought(DraftSig)  # hidden reasoning
    Critic = dspy.Predict(CriticSig)
    Revise = dspy.Predict(ReviseSig)

    # ---- token budgeting against the real model id ----
    limit_probe = [
        {"role": "system", "content": "You are a structured JSON generator."},
        {"role": "user", "content": f"Instructions:\n{system_msg}\n\nTask:\n{user_msg}\n\nSchema:\n{schema_json}\n\nReturn ONLY JSON."},
    ]
    try:
        safe_tokens = int(limit_tokens(limit_probe, max_output_tokens, 'dspy'))
    except Exception:
        safe_tokens = min(max_output_tokens, 1024)

    # ---- Draft → Critic → Revise loop ----
    with dspy.context(lm=dspy_lm):
        draft = Draft(
            sys_instructions=system_msg,
            task=user_msg,
            json_schema=schema_json,
            max_tokens=safe_tokens,
            temperature=temperature,
        ).json_out

        normalized = parse_json(draft) # clean and check JSON
        validated = structure_model.model_validate(normalized)

        if isinstance(validated, structure_model):
            return normalized

        issues_text = "Output did not validate against schema."
        candidate   = draft
        for _ in range(max(1, retries)):
            critique = Critic(
                sys_instructions=system_msg,
                task=user_msg,
                json_schema=schema_json,
                candidate=candidate,
                max_tokens=min(512, safe_tokens // 2),
                temperature=0.0,  # make the critic deterministic
            ).issues

            if critique.strip().lower() != "no issues":
                issues_text = (issues_text + "\n\nAdditional critique:\n" + critique).strip()

            candidate = Revise(
                sys_instructions=system_msg,
                task=user_msg,
                json_schema=schema_json,
                candidate=candidate,
                issues=issues_text,
                max_tokens=safe_tokens,
                temperature=temperature,
            ).json_out

            normalized = parse_json(candidate)
            validated = structure_model.model_validate(normalized)

            if isinstance(validated, structure_model):
                return normalized
            
            issues_text = f"Output did not validate against schema."

        # last attempt
        final_try = Revise(
            sys_instructions=system_msg,
            task=user_msg,
            json_schema=schema_json,
            candidate=candidate,
            issues=issues_text + "\nReturn ONLY a valid JSON object with no extra text.",
            max_tokens=safe_tokens,
            temperature=temperature,
        ).json_out

        normalized = parse_json(final_try)
        validated = structure_model.model_validate(normalized)

        if isinstance(validated, structure_model):
            return normalized

        err = f"Final output did not validate against schema"

    raise ValueError(f"DSPy structured generation failed: {err}")


def produce_structured_response_gemini(
    prompt: str,
    structure_model: Type[BaseModel],
    llm_model: str = "gemini-2.5-pro",
) -> Any:
    """Gemini structured response implementation."""
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=llm_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": structure_model,
            },
        )
        # Parse JSON response into the Pydantic model
        json_text = response.candidates[0].content.parts[0].text
        return structure_model.model_validate_json(json_text)
    except Exception as e:
        logger.error(f"Gemini structured response generation failed: {e}")
        raise


def format_messages_for_api(
    system_message: Optional[str] = None,
    user_message: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """
    Helper to format messages for API calls.
    """
    if messages:
        return messages

    formatted: List[Dict[str, str]] = []
    if system_message:
        formatted.append({"role": "system", "content": system_message})
    if user_message:
        formatted.append({"role": "user", "content": user_message})
    return formatted


# ==========================================
# Backward Compatibility Exports (Preserved)
# ==========================================
llm_gpt5 = _llm_gpt5

