"""
Simplified LLM interface for evaluator to avoid import dependencies.
"""
import os
import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
import requests

parse_json = lambda x: x

try:
    from utils.json_repair import parse_json as import_parse_json
    parse_json = import_parse_json
except ImportError:
    from incept_core.utils.json_repair import parse_json as import_parse_json
    parse_json = import_parse_json

logger = logging.getLogger(__name__)

def simple_solve_with_llm(
    messages: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Simplified LLM interface that only uses OpenAI to avoid dependency issues.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    client = OpenAI(api_key=api_key)

    try:
        resp = client.responses.create(
            model='gpt-4o',
            input=messages,
            max_output_tokens=16000,
        )

        raw_text = resp.output_text
        response = parse_json(raw_text)

        return response
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        # Return default scores on failure
        return {
            "scores": {
                "correctness": 5,
                "grade_alignment": 5,
                "difficulty_alignment": 5,
                "language_quality": 5,
                "pedagogical_value": 5,
                "explanation_quality": 5,
                "instruction_adherence": 5,
                "format_compliance": 5
            },
            "issues": [f"LLM call failed: {str(e)}"],
            "strengths": [],
            "suggested_improvements": ["Fix LLM connectivity"],
            "recommendation": "revise"
        }

def simple_solve_with_llm_falcon(
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    safe_max_tokens: int = 5000,
) -> Dict[str, Any]:
    """
    Simplified LLM interface that only uses Falcon to avoid dependency issues.
    """
    model = "tiiuae/Falcon-H1-34B-Instruct"
    base_url = "http://69.19.137.5:8000/v1"
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(safe_max_tokens),
        "messages": messages,
    }

    resp = requests.post(url, json=payload, timeout=1800)
    if resp.status_code != 200:
        logger.error(f"Falcon API error: {resp.status_code} - {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    return content