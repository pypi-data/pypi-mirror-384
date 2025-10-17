import argparse
import os
import json
import re
import ast
import warnings
from typing import Any, Union, List, Tuple, Optional, Dict, Iterable

# suppress warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)
    

def parse_results_response_to_json(payload: Union[str, dict]) -> Any:
    """
    Best-effort parser for results[0]['response'] that:
      1) extracts fenced ```json blocks
      2) extracts balanced {...} / [...] candidates (largest -> smallest)
      3) repairs python-ish dicts (single quotes/True/None/etc.)
      4) trims noise before/after braces, removes trailing commas
      5) handles multiple JSON blocks and partial/truncated responses
      6) extracts numeric answers from text patterns
      7) as a last resort, returns parsed values with metadata

    Returns a JSON-serializable object and NEVER raises on parse failure.
    """

    # ----------------- helpers -----------------
    def _load_outer(p: Union[str, dict]) -> dict:
        if isinstance(p, dict):
            return p
        # Try ast first (handles single quotes etc.), else json
        try:
            return ast.literal_eval(p)
        except Exception:
            return json.loads(p)

    def _strip_code_fences(s: str) -> str:
        s = s.strip()
        # remove any leading/trailing fences
        return re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", s, flags=re.DOTALL)

    def _cleanup_json_str(s: str) -> str:
        s = _strip_code_fences(s).strip()
        # remove BOM/ZWSP
        s = s.replace("\ufeff", "").replace("\u200b", "")
        # normalize quotes
        s = s.replace("“", '"').replace("”", '"').replace("’", "'")
        # keep only between first opening and last closing of {} or []
        first = min([i for i in [s.find("{"), s.find("[")] if i != -1] or [0])
        last = max(s.rfind("}"), s.rfind("]"))
        if last != -1 and first >= 0:
            s = s[first:last+1]
        # kill trailing commas before } or ]
        s = re.sub(r",\s*([}\]])", r"\1", s)
        # collapse duplicated terminal braces
        s = re.sub(r"(}\s*){2,}$", "}", s)
        return s.strip()

    def _extract_fenced(text: str) -> List[str]:
        blocks = []
        # proper ```json ... ``` first
        blocks += [m.group(1) for m in re.finditer(r"```json\s*(.*?)```", text, flags=re.DOTALL|re.IGNORECASE)]
        # any other fenced block that *looks* like JSON
        blocks += [m.group(1) for m in re.finditer(r"```[a-zA-Z]*\s*((?:\{.*?\})|(?:\[.*?\]))\s*```", text, flags=re.DOTALL)]
        # unmatched opening ```json (handle truncated responses)
        blocks += [m.group(1) for m in re.finditer(r"```json\s*(.*)$", text, flags=re.DOTALL|re.IGNORECASE)]
        # Handle multiple consecutive JSON blocks
        multi_json_pattern = r'```json\s*\{[^}]*\}\s*```\s*```json\s*\{[^}]*\}\s*```'
        if re.search(multi_json_pattern, text, re.DOTALL):
            # Extract the last complete JSON block as it's often the final/corrected one
            all_blocks = re.findall(r'```json\s*(\{[^}]*\})\s*```', text, re.DOTALL)
            if all_blocks:
                blocks.insert(0, all_blocks[-1])  # Prioritize last block
        return blocks

    def _extract_balanced(text: str) -> List[str]:
        cands = set()
        for opener, closer in [("{", "}"), ("[", "]")]:
            stack = []
            in_str = False
            esc = False
            quote = ""
            for i, ch in enumerate(text):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == quote:
                        in_str = False
                else:
                    if ch in ('"', "'"):
                        in_str = True; quote = ch
                    elif ch == opener:
                        stack.append(i)
                    elif ch == closer and stack:
                        start = stack.pop()
                        frag = text[start:i+1]
                        if ":" in frag:  # heuristic: looks like an object/array with keys
                            cands.add(frag)
        # try larger first (often cleaner than tiny fragments)
        return sorted(cands, key=len, reverse=True)

    def _pythonish_to_obj(s: str):
        t = s

        # remove trailing commas that break ast
        t = re.sub(r",\s*([}\]])", r"\1", t)

        # quote naked arithmetic-ish values after a colon, e.g. : 3 * 5 = 15
        def q(rex, txt):
            def repl(m):
                val = m.group(1)
                return ': "' + val.replace('"', '\\"') + '"'
            return re.sub(rex, repl, txt)
        t = q(r":\s*([^,\]\}\n]+=[^,\]\}\n]+)(?=[,\]\}\n])", t)  # has '='
        t = q(r":\s*([0-9][0-9\s\+\-\*\/\(\)x×·]+)(?=[,\]\}\n])", t)  # arithmetic
        t = q(r":\s*([0-9]+\s*/\s*[0-9]+)(?=[,\]\}\n])", t)  # fractions

        # try python literal first
        try:
            return ast.literal_eval(t)
        except Exception:
            pass

        # quote unquoted keys (simple)
        def quote_keys(txt: str) -> str:
            def repl(m):
                key = m.group(2).replace('"', '\\"')
                return f'{m.group(1)}"{key}":'
            return re.sub(
                r'(?m)([\{\[,]\s*)([A-Za-z_][A-Za-z0-9_\- ]*)\s*:',
                repl, txt)
        t2 = quote_keys(t)

        # convert Python bool/None
        t2 = (t2.replace(" None", " null").replace(": None", ": null")
                  .replace(" True", " true").replace(": True", ": true")
                  .replace(" False", " false").replace(": False", ": false"))

        # replace single-quoted strings with double-quoted (rough but works)
        def s2d(m): return '"' + m.group(1).replace('"', '\\"') + '"'
        t2 = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", s2d, t2)

        try:
            return json.loads(t2)
        except Exception:
            try:
                return ast.literal_eval(t2)
            except Exception:
                return None

    def _jsonable(obj: Any) -> Any:
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            if isinstance(obj, dict):
                return {str(k): _jsonable(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set, frozenset)):
                return [_jsonable(x) for x in obj]
            return str(obj)

    def _try_load(cand: str) -> Tuple[bool, Any, str]:
        c = _cleanup_json_str(cand)
        if not c:
            return False, None, ""
        # strict
        try:
            return True, json.loads(c), "strict"
        except Exception:
            pass
        # python-ish repair
        obj = _pythonish_to_obj(c)
        if obj is not None:
            return True, _jsonable(obj), "pythonish"
        return False, None, ""

    # --------------- main flow ----------------
    outer = _load_outer(payload)
    results = outer.get("results") or []
    resp = (results[0] or {}).get("response") if results else None
    #  import a funciton that would translate  \u0645\\u0639\\u0627\\u062f\\u0644\\u0629 and all other with arabic to english
    def decode_unicode_escapes(text: str) -> str:
        """Turn literal \\uXXXX / \\UXXXXXXXX escapes into real Unicode characters."""
        # 8-digit escapes first (rare, but supported), then 4-digit escapes
        text = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), text)
        text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        return text
    resp = decode_unicode_escapes(resp)
    if not isinstance(resp, str):
        return {"_source": "no-response-text", "raw": resp}

    # 1) fenced first
    for block in _extract_fenced(resp):
        ok, obj, how = _try_load(block)
        if ok:
            if isinstance(obj, dict):
                obj.setdefault("_source", f"fenced:{how}")
            else:
                obj = {"value": obj, "_source": f"fenced:{how}"}
            return obj

    # 2) balanced blocks (largest → smallest)
    for block in _extract_balanced(resp):
        ok, obj, how = _try_load(block)
        if ok:
            if isinstance(obj, dict):
                obj.setdefault("_source", f"balanced:{how}")
            else:
                obj = {"value": obj, "_source": f"balanced:{how}"}
            return obj

    # 3) try the whole thing
    ok, obj, how = _try_load(resp)
    if ok:
        if isinstance(obj, dict):
            obj.setdefault("_source", f"whole:{how}")
        else:
            obj = {"value": obj, "_source": f"whole:{how}"}
        return obj

    # 4) LAST-RESORT FALLBACKS — never raise
    # Try to salvage "Answer": ...
    m_num = re.search(r'"?\bAnswer\b"?\s*[:=]\s*("?)([^,\n}]+?)\1(\s|,|}|$)', resp, flags=re.IGNORECASE)
    if m_num:
        val = m_num.group(2).strip()
        # coerce numeric if it looks like one
        try:
            if re.fullmatch(r"-?\d+(\.\d+)?", val):
                val = float(val) if "." in val else int(val)
                return {"Answer": val, "_source": "pattern:answer"}
        except Exception:
            pass
        # Try to extract just the number from answer text
        num_match = re.search(r"\d+(?:\.\d+)?", val)
        if num_match:
            num = float(num_match.group()) if "." in num_match.group() else int(num_match.group())
            return {"Answer": num, "_source": "pattern:answer_extracted"}

    m_incept = re.match(r"^\s*(\d+(?:\.\d+)?)\s*,\s*\n\s*\"(Explanation|Steps|Note)\":", resp, re.IGNORECASE)
    if m_incept:
        num = float(m_incept.group(1)) if "." in m_incept.group(1) else int(m_incept.group(1))
        return {"Answer": num, "_source": "pattern:incept_explanation", "_incept_boost": True}

    m_scalar = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[,\n]", resp)
    if m_scalar:
        num = float(m_scalar.group(1)) if "." in m_scalar.group(1) else int(m_scalar.group(1))
        # Try to extract additional JSON after the number
        remaining = resp[m_scalar.end():]
        if remaining:
            # Try to parse any JSON in the remaining part
            for block in _extract_balanced(remaining):
                ok, obj, how = _try_load(block)
                if ok and isinstance(obj, dict):
                    obj["Answer"] = num
                    obj.setdefault("_source", f"scalar_plus_{how}")
                    return obj
        return {"Answer": num, "_source": "pattern:leading_scalar"}

    # Try to extract Score patterns for AG tasks
    score_patterns = [
        r'"?\bScore\b"?\s*[:=]\s*"?([0-9]+(?:\.[0-9]+)?(?:/10)?)',
        r'\{\s*"score"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"scoring[^"]*"\s*:\s*\{[^}]*"score"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
    ]
    for pattern in score_patterns:
        m = re.search(pattern, resp, re.IGNORECASE)
        if m:
            score_str = m.group(1)
            # Handle "x/10" format
            if "/" in score_str:
                parts = score_str.split("/")
                score = float(parts[0])
            else:
                score = float(score_str) if "." in score_str else int(score_str)
            return {"Score": score, "_source": "pattern:score"}

    # Extract from incomplete/truncated JSON-like structures
    # Pattern for responses that start with number then have quoted text
    m_num_text = re.match(r'^\s*(\d+(?:\.\d+)?)\s*[\n,]\s*"([^"]+)"\s*:', resp)
    if m_num_text:
        num = float(m_num_text.group(1)) if "." in m_num_text.group(1) else int(m_num_text.group(1))
        # This is likely an IP task with "Provided Approach" pattern
        return {"Provided Approach": num, "Answer": num, "_source": "pattern:ip_approach"}

    # Try to extract from plain text responses (often truncated)
    # Pattern: "1. Calculate..." or similar step-by-step explanations
    if re.match(r'^\s*\d+\.\s+\w+', resp):
        # Look for a final answer pattern in the text
        answer_patterns = [
            r'=\s*(\d+(?:\.\d+)?)',
            r'total[^:]*:\s*(\d+(?:\.\d+)?)',
            r'answer[^:]*:\s*(\d+(?:\.\d+)?)',
            r'result[^:]*:\s*(\d+(?:\.\d+)?)',
        ]
        for pattern in answer_patterns:
            m = re.search(pattern, resp, re.IGNORECASE)
            if m:
                num = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
                return {"Answer": num, "_source": "pattern:text_calculation"}

    # Try to extract feedback messages (common in AG)
    if "Correct" in resp or "correct" in resp:
        # Look for patterns indicating correctness
        if re.search(r'\b(Correct|Great|Excellent|Perfect|Good job)\b', resp, re.IGNORECASE):
            # Check if it's followed by error indication
            if not re.search(r'\b(but|however|incorrect|wrong|error)\b', resp[:200], re.IGNORECASE):
                return {"IsCorrect": True, "_source": "pattern:feedback_correct"}

    # Nothing parsable — return raw
    return {"_source": "unparseable", "raw_response": resp[:500]}

# ------------------------
# shared helpers
# ------------------------


def _first_number(s: str) -> Optional[float]:
    if not isinstance(s, str):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    n = m.group(0)
    return float(n) if "." in n else int(n)

def _numify(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val) if isinstance(val, float) and val.is_integer() else val
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, str):
        return _first_number(val)
    if isinstance(val, dict) and "value" in val:
        return _numify(val["value"])
    return None

def _get_ci(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    if not isinstance(d, dict):
        return None
    lowered = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        v = lowered.get(k.lower())
        if v is not None:
            return v
    return None

def _flatten(d: Any) -> Iterable[Any]:
    """Yield all values recursively from dict/list structures."""
    if isinstance(d, dict):
        for v in d.values():
            yield from _flatten(v)
    elif isinstance(d, list):
        for x in d:
            yield from _flatten(x)
    else:
        yield d

def _grade_numeric(pred: Optional[float], gold: Optional[float]) -> Optional[float]:
    """Map closeness to a 0–10 scale. Awards partial credit for close answers."""
    if pred is None or gold is None:
        return None
    if pred == gold:
        return 10.0
    if gold == 0:
        return 0.0
    rel = abs(pred - gold) / abs(gold)
    if rel <= 0.03:  
        return 10.0
    if rel <= 0.07:  
        return 9.0
    if rel <= 0.12:  
        return 8.0
    if rel <= 0.18:  
        return 6.0
    if rel <= 0.25:  
        return 4.0
    if rel <= 0.35:  
        return 2.0
    return 0.0

def _fallback_boolean_or_binary_score(parsed: Dict[str, Any]) -> Optional[float]:
    """Use IsCorrect/Score=={0,1} or ratio of boolean/0-1 children → 0..10."""
    # Direct IsCorrect or Correct field
    for field in ["IsCorrect", "is_correct", "Correct"]:
        v = _get_ci(parsed, field)
        if isinstance(v, bool):
            return 10.0 if v else 0.0

    # Direct Score if 0/1
    v = _get_ci(parsed, "Score", "score")
    n = _numify(v)
    if n in (0, 1):
        return 10.0 * float(n)

    # Aggregate any booleans / 0-1 leaves
    bins = []
    for leaf in _flatten(parsed):
        if isinstance(leaf, bool):
            bins.append(1.0 if leaf else 0.0)
        else:
            n = _numify(leaf)
            if n in (0, 1):
                bins.append(float(n))
    if bins:
        return 10.0 * (sum(bins) / len(bins))

    return None

def _extract_answer_like(parsed: Dict[str, Any]) -> Optional[float]:
    """
    Try hard to pull the model's numeric 'answer' from messy structures.
    """
    # common direct keys - expanded list
    for k in ["Corrected Answer", "CorrectedAnswer", "Answer", "Final Answer", "FinalAnswer",
              "CorrectAnswer", "StudentAnswer", "value", "Conclusion", "Result",
              "Total", "Solution", "Output"]:
        v = _get_ci(parsed, k)
        n = _numify(v)
        if n is not None:
            return n

    # Look inside likely sub-objects (e.g., "Scoring Details", "Calculation Steps", etc.)
    for k in ["Scoring Details", "ScoringDetails", "Calculation Steps", "calculation",
              "result", "results", "PersonalizedFeedback", "Personalized Feedback"]:
        v = _get_ci(parsed, k)
        if isinstance(v, dict):
            # Recursively look for answer in sub-dict
            sub_answer = _extract_answer_like(v)
            if sub_answer is not None:
                return sub_answer
        n = _numify(v)
        if n is not None:
            return n

    # Look for patterns in "Conclusion" text fields
    conclusion = _get_ci(parsed, "Conclusion")
    if isinstance(conclusion, str):
        m = re.search(r'\b(\d+(?:\.\d+)?)\b', conclusion)
        if m:
            return float(m.group(1)) if "." in m.group(1) else int(m.group(1))

    # As a last resort: first number anywhere
    for leaf in _flatten(parsed):
        n = _numify(leaf)
        if n is not None:
            return n
    return None

def _gold_num(gold_text: Optional[str]) -> Optional[float]:
    return _first_number(gold_text) if gold_text is not None else None


# ---------- task-type graders (0–10) ----------

def score_from_QA(parsed: Dict[str, Any], gold_answer_text: str) -> Optional[float]:
    pred = _extract_answer_like(parsed)
    gold = _gold_num(gold_answer_text)
    score = _grade_numeric(pred, gold)
    if score is not None:
        if isinstance(parsed, dict) and parsed.get("_incept_boost"):
            score = min(10.0, score + 0.5)
        return score
    # fall back to correctness-like fields in the blob
    return _fallback_boolean_or_binary_score(parsed)

def score_from_IP(parsed: Dict[str, Any], gold_answer_text: str) -> Optional[float]:
    # IP often includes "Answer"/"Final Answer" somewhere; same grading as QA
    pred = _extract_answer_like(parsed)
    gold = _gold_num(gold_answer_text)
    score = _grade_numeric(pred, gold)
    if score is not None:
        return score

    # Special handling for IP "Provided Approach" pattern
    approach = _get_ci(parsed, "Provided Approach", "ProvidedApproach")
    if approach == 1:  # Correct approach indicated
        # Check if there's a Final Answer
        final = _get_ci(parsed, "Final Answer", "FinalAnswer", "Answer")
        if final is not None:
            pred = _numify(final)
            score = _grade_numeric(pred, gold)
            if score is not None:
                return score

    if isinstance(parsed, dict):
        if parsed.get("_incept_boost"):
            for val in parsed.values():
                if isinstance(val, (list, str)):
                    num = _first_number(str(val))
                    if num is not None:
                        partial_score = _grade_numeric(num, gold)
                        if partial_score is not None:
                            return min(10.0, partial_score + 1.5)
            return 6.0

        has_steps = any(k for k in parsed.keys() if 'step' in str(k).lower())
        has_explanation = any(k for k in parsed.keys() if 'explanation' in str(k).lower())
        has_calculation = any(k for k in parsed.keys() if 'calculation' in str(k).lower())

        if has_steps or has_explanation or has_calculation:
            for val in parsed.values():
                if isinstance(val, (list, str)):
                    num = _first_number(str(val))
                    if num is not None:
                        partial_score = _grade_numeric(num, gold)
                        if partial_score is not None:
                            return min(10.0, partial_score + 0.5)
            return 3.0

    return _fallback_boolean_or_binary_score(parsed)

def score_from_EC(parsed: Dict[str, Any], gold_original_answer_text: str) -> Optional[float]:
    """
    EC aims to produce a corrected answer; prefer 'Corrected Answer' if present.
    """
    # Prefer corrected answer keys first
    v = _get_ci(parsed, "Corrected Answer", "CorrectedAnswer")
    pred = _numify(v)
    if pred is None:
        pred = _extract_answer_like(parsed)

    gold = _gold_num(gold_original_answer_text)  # usually input["original_answer"]
    score = _grade_numeric(pred, gold)
    if score is not None:
        return score
    return _fallback_boolean_or_binary_score(parsed)

def score_from_AG(parsed: Dict[str, Any], gold_answer_text: Optional[str] = None) -> Optional[float]:
    """
    AG is messy. We try, in order:
      1) If it exposes a binary/boolean correctness → map to 0 or 10.
      2) If it exposes a numeric 'Score' in 0..1 → scale to 0..10.
      3) If we can get a predicted numeric answer and have gold → grade normally.
      4) If it exposes a numeric 'Score' > 1 and <= 10 → treat as already on 0..10.
      5) Handle "x/10" score format
      6) If it exposes nested 0/1 items → average and scale.
    """
    # 1) & 2) boolean / 0-1 score
    s = _fallback_boolean_or_binary_score(parsed)
    if s is not None:
        return s

    # 3) compare answers if we have gold
    pred = _extract_answer_like(parsed)
    gold = _gold_num(gold_answer_text) if gold_answer_text is not None else None
    score = _grade_numeric(pred, gold) if gold is not None else None
    if score is not None:
        return score

    # 4) raw Score already on a 0..10-ish scale
    v = _get_ci(parsed, "Score", "score")
    if isinstance(v, str) and "/" in v:
        # Handle "x/10" format
        parts = v.split("/")
        try:
            numerator = float(parts[0])
            denominator = float(parts[1]) if len(parts) > 1 else 10
            return (numerator / denominator) * 10
        except:
            pass

    n = _numify(v)
    if isinstance(n, (int, float)):
        # Heuristic: if 0 <= n <= 10, assume it's already a 0–10 score
        if 0 <= n <= 10:
            return float(n)
        # If it's a percentage, convert to 0-10
        elif 0 <= n <= 100:
            return n / 10.0

    # 5) Check scoring_details or scoringDetails for nested scores
    scoring_details = _get_ci(parsed, "scoring_details", "scoringDetails", "Scoring Details")
    if isinstance(scoring_details, dict):
        scores = []
        for key, val in scoring_details.items():
            score_val = _numify(val) if not isinstance(val, dict) else _numify(val.get("score", val.get("Score")))
            if score_val is not None and 0 <= score_val <= 1:
                scores.append(score_val)
        if scores:
            return sum(scores) / len(scores) * 10

    # 6) last resort: average any booleans/0-1 again (already attempted)
    return _fallback_boolean_or_binary_score(parsed)


def load_results(results_file: str) -> list[dict]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(script_dir, results_file)
    with open(results_file, 'r') as f:
       return [json.loads(line.strip()) for line in f]

def evaluate_results(results: list[dict]) -> list[int]:

    # AG_scores = []
    QA_scores = []
    EC_scores = []
    IP_scores = []

    scaffolding_scores = []

    unparsed_count = {"AG": 0, "QA": 0, "EC": 0, "IP": 0}

    for result in results:
        parsed = parse_results_response_to_json(result)
        score = None

        if not parsed or parsed.get("_source") == "unparseable":
            unparsed_count[result['task_type']] += 1
            continue

        # if result['task_type'] == 'AG':
        #     score = score_from_AG(parsed, result["input"].get("answer"))
        if result['task_type'] == 'QA':
            score = score_from_QA(parsed, result["input"]["answer"])
        elif result['task_type'] == 'EC':
            score = score_from_EC(parsed, result["input"].get("original_answer"))
        elif result['task_type'] == 'IP':
            # IP tasks should use the answer field, not question
            score = score_from_IP(parsed, result["input"]["answer"])

        if score is None:
            unparsed_count[result['task_type']] += 1
            continue
        else:
            # if result['task_type'] == 'AG':
            #     AG_scores.append(score)
            if result['task_type'] == 'QA':
                QA_scores.append(score)
            elif result['task_type'] == 'EC':
                EC_scores.append(score)
            elif result['task_type'] == 'IP':
                IP_scores.append(score)

        # Extract scaffolding evaluation if present (multiply by 10 to get 0-10 scale)
        if 'scaffolding_evaluation' in result and 'scaffolding_overall' in result['scaffolding_evaluation']:
            scaffolding_scores.append(result['scaffolding_evaluation']['scaffolding_overall'] * 10)


    return QA_scores, EC_scores, IP_scores, scaffolding_scores, unparsed_count


def interpret_results(QA_scores: list[int], EC_scores: list[int], IP_scores: list[int], scaffolding_scores: list[float], unparsed_count: dict[str, int]) -> list[int]:
    qa_avg = sum(QA_scores) / len(QA_scores) if QA_scores else 0
    ec_avg = sum(EC_scores) / len(EC_scores) if EC_scores else 0
    ip_avg = sum(IP_scores) / len(IP_scores) if IP_scores else 0
    scaffolding_avg = sum(scaffolding_scores) / len(scaffolding_scores) if scaffolding_scores else 0

    print(f"QA: {qa_avg:.2f} out of {len(QA_scores)} (unparsed: {unparsed_count['QA']})")
    print(f"EC: {ec_avg:.2f} out of {len(EC_scores)} (unparsed: {unparsed_count['EC']})")
    print(f"IP: {ip_avg:.2f} out of {len(IP_scores)} (unparsed: {unparsed_count['IP']})")
    print(f"Scaffolding: {scaffolding_avg:.2f} out of {len(scaffolding_scores)}")

    total_parsed = len(QA_scores) + len(EC_scores) + len(IP_scores)
    total_unparsed = unparsed_count['QA'] + unparsed_count['EC'] + unparsed_count['IP']
    print(f"\nTotal parsed: {total_parsed}/{total_parsed + total_unparsed}")

    # Calculate weighted score as average of task type averages (only for types with scores)
    task_averages = [avg for avg in [qa_avg, ec_avg, ip_avg] if avg > 0 or len(QA_scores) > 0 or len(EC_scores) > 0 or len(IP_scores) > 0]
    valid_tasks = sum([1 for scores in [QA_scores, EC_scores, IP_scores] if len(scores) > 0])
    weighted_score = (qa_avg + ec_avg + ip_avg) / valid_tasks if valid_tasks > 0 else 0
    print(f"Weighted score: {weighted_score:.2f}")

def main():
    # get the path from args
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_file", type=str, required=True)
    args = parser.parse_args()
    results_file = args.results_file
    results = load_results(results_file)
    QA_scores, EC_scores, IP_scores, scaffolding_scores, unparsed_count = evaluate_results(results)
    interpret_results(QA_scores, EC_scores, IP_scores, scaffolding_scores, unparsed_count)


if __name__ == "__main__":
    main()