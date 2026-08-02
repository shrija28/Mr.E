"""Groq client wiring and prompt helpers.

This is the LLM-facing layer of the RAG pipeline.  The client itself is
constructed lazily so that importing the package does not crash when
``GROQ_API_KEY`` is missing - the legacy app raised at import time which
made unit tests difficult.  ``smartkcet.main`` still calls
:func:`get_groq_client` on startup so the failure mode is preserved for the
runtime entry point.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Iterable, List, Optional, Set

from groq import Groq

from ..config import require_groq_api_key

logger = logging.getLogger("smartkcet.rag.groq_client")

_client: Optional[Groq] = None


class GroqAPIKeyError(ValueError):
    """Raised when the Groq API key is missing, placeholder, or invalid."""
    pass


def _mask_key(key: str) -> str:
    """Return a masked version of the API key for logging (e.g., gsk_xxx***)."""
    if not key:
        return "(empty)"
    if len(key) <= 8:
        return key[:3] + "***"
    return key[:7] + "***" + key[-3:]


def validate_groq_api_key() -> str:
    """Validate the Groq API key at startup. Returns the key or raises GroqAPIKeyError."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise GroqAPIKeyError(
            "GROQ_API_KEY is not set in the environment. "
            "Add it to backend/.env file."
        )

    # Detect common placeholder values
    placeholders = {
        "your-groq-api-key-here",
        "your_groq_api_key",
        "sk-xxx",
        "gsk_xxx",
        "CHANGE_ME",
        "placeholder",
        "your-api-key",
    }
    if api_key.lower() in placeholders or api_key.startswith("your-"):
        raise GroqAPIKeyError(
            f"GROQ_API_KEY appears to be a placeholder value ({_mask_key(api_key)}). "
            "Get a real API key from https://console.groq.com/keys"
        )

    # Groq keys typically start with "gsk_"
    if not api_key.startswith("gsk_"):
        logger.warning(
            "GROQ_API_KEY does not start with 'gsk_' (got: %s). "
            "This may be invalid. Groq API keys typically start with 'gsk_'.",
            _mask_key(api_key),
        )

    logger.info("GROQ_API_KEY detected: %s", _mask_key(api_key))
    return api_key


def get_groq_client() -> Groq:
    """Return a process-wide Groq client, creating it on first use."""

    global _client
    if _client is None:
        api_key = validate_groq_api_key()
        _client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully (model: llama-3.3-70b-versatile)")
    return _client


def reset_groq_client() -> None:
    """Force re-creation of the Groq client on next use. Call after .env changes."""
    global _client
    _client = None


def create_chat_completion_with_fallback(client: Groq, **kwargs) -> Any:
    """Wrapper around client.chat.completions.create that implements automatic
    fallback to llama-3.1-8b-instant/instruct on 429 rate limit errors.
    If the API key is an Nvidia NIM key (starts with nvapi-), it uses Nvidia API
    endpoints and models instead.
    """
    import time
    import httpx
    
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    is_nvidia = api_key.startswith("nvapi-")
    
    if is_nvidia:
        # Nvidia configurations
        primary_model = os.getenv("GROQ_MODEL", "meta/llama-3.1-8b-instruct")
        fallback_model = "meta/llama-3.1-8b-instruct"
    else:
        # Groq configurations
        primary_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        fallback_model = "llama-3.1-8b-instant"

    kwargs["model"] = primary_model

    # Clamp max_tokens to prevent "Request too large" (TPM limit on free tier)
    if "max_tokens" in kwargs and kwargs["max_tokens"] > 2500:
        kwargs["max_tokens"] = 2500

    max_retries = 3
    base_delay = 5.0

    for attempt in range(max_retries + 1):
        try:
            if is_nvidia:
                # Custom HTTP request to Nvidia API catalog
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                json_body = {
                    "model": kwargs["model"],
                    "messages": kwargs.get("messages", []),
                    "temperature": kwargs.get("temperature", 0.4),
                }
                if "max_tokens" in kwargs:
                    json_body["max_tokens"] = kwargs["max_tokens"]
                
                resp = httpx.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers,
                    json=json_body,
                    timeout=180.0
                )
                
                if resp.status_code != 200:
                    raise RuntimeError(f"Nvidia API call failed with status {resp.status_code}: {resp.text}")
                
                data = resp.json()
                
                # Wrap response in OpenAI-compatible shape
                class Message:
                    def __init__(self, content):
                        self.content = content
                        self.role = "assistant"
                class Choice:
                    def __init__(self, message):
                        self.message = message
                class Response:
                    def __init__(self, content):
                        self.choices = [Choice(Message(content))]
                
                content = data["choices"][0]["message"]["content"]
                return Response(content)
            else:
                # Normal Groq request
                return client.chat.completions.create(**kwargs)
                
        except Exception as exc:
            exc_str = str(exc).lower()
            
            # Check if this is a rate limit, payload size error, or timeout (429, 413, or timeout)
            is_rate_limit = (
                "rate_limit" in exc_str or 
                "429" in exc_str or 
                "rate limit" in exc_str or 
                "413" in exc_str or 
                "too large" in exc_str or
                "exceeded" in exc_str or
                "timeout" in exc_str
            )
            
            if is_rate_limit:
                # Switch to fallback model if we're currently on the primary model
                if kwargs["model"] == primary_model:
                    logger.warning(
                        f"Rate limit hit for primary model {primary_model}. "
                        f"Switching to fallback model {fallback_model}..."
                    )
                    kwargs["model"] = fallback_model
                    time.sleep(1.0)
                    continue
                
                # If we have retries left, wait and retry
                if attempt < max_retries:
                    sleep_time = base_delay * (2 ** attempt)
                    match = re.search(r"try again in ([0-9\.]+)(s|m|h)", exc_str)
                    if match:
                        val = float(match.group(1))
                        unit = match.group(2)
                        if unit == "s":
                            sleep_time = val + 0.5
                        elif unit == "m":
                            sleep_time = (val * 60) + 1.0
                    
                    logger.warning(
                        f"Rate limit hit. Sleeping for {sleep_time:.2f}s before retry {attempt + 1}/{max_retries}..."
                    )
                    time.sleep(sleep_time)
                    continue
            raise


def parse_llm_json(raw: str) -> List[dict]:
    """Robustly extract a JSON array of question dicts from an LLM response."""

    original = raw
    raw = raw.strip()
    raw = re.sub(r"^```(?:json|)\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
    except json.JSONDecodeError as exc:
        print(f"Direct JSON parse failed: {exc}")
    try:
        match = re.search(r"\[\s*\{.*?\}\s*\]", original, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if isinstance(data, list):
                return data
    except Exception:
        pass
    print("Failed to parse JSON completely.")
    return []


def generate_mcq_set(
    context_chunks: Iterable[str],
    subject: str,
    set_label: str,
    used_questions: Set[str],
) -> List[dict]:
    """Generate a 20-question MCQ set for ``subject`` using ``context_chunks``."""

    chunks = list(context_chunks)
    context = "\n\n".join(chunks[:8])
    used_str = (
        "\n".join(f"- {q}" for q in list(used_questions)[:20])
        if used_questions
        else "None"
    )

    prompt = f"""You are creating a 20-question MCQ exam paper (Set {set_label}) for: {subject}.
This is a Karnataka Common Entrance Test (KCET) level exam.

Below is the actual content from uploaded question papers. Use ONLY these topics:
---
{context}
---

Questions already used in other sets (DO NOT repeat these):
{used_str}

STRICT KCET EXAM RULES:
1. NO TRIVIAL/FACTUAL DEFINITIONS: Do NOT ask simple fact-retrieval questions (e.g. 'What is the main objective of...', 'Who discovered...', 'Define the term...').
2. HIGH-QUALITY PROBLEMS: Every question must be a problem-solving, calculation, application-based, or rigorous conceptual deduction question.
3. SUBJECT-SPECIFIC STANDARDS:
   - Mathematics: Focus on calculation-heavy problems (e.g., calculus/derivatives/integrals, limits, matrix order/determinant properties, vector dot/cross products, trigonometry simplifications, relations/functions/mappings). Use mathematical equations and variables in the question stem.
   - Physics: Formulate numerical problems applying physics formulas (e.g., electrostatics, circuit dynamics, mechanics, thermodynamics, wave optics). 
   - Chemistry: Include stoichiometry calculations, organic reactions (reagents, products), physical chemistry numericals (kinetics, chemical equilibrium), electronic configurations.
   - Biology: Focus on deep understanding, genetic crosses (Mendelian ratios), physiological mechanisms, cellular stages.
4. STYLE & CONCISENESS: Keep the question stem brief, precise, and containing clear mathematical/scientific conditions.
5. MATHEMATICAL EXAMPLES (Use this style for Mathematics):
   - Example 1: "If Set A has 4 elements and set B has 5 elements, then the number of injective mappings that can be defined from A to B is:" Options: ["144", "72", "60", "120"], Answer: 3
   - Example 2: "The value of sin^-1(cos(53*pi/5)) is:" Options: ["3*pi/5", "-3*pi/5", "pi/10", "-pi/10"], Answer: 3
   - Example 3: "If A is any square matrix of order 3x3, then |3A| is equal to:" Options: ["3|A|", "1/3|A|", "27|A|", "9|A|"], Answer: 2
   - Example 4: "If y = e^(sin^-1(t^2-1)) and x = e^(sec^-1(1/(t^2-1))), then dy/dx is equal to:" Options: ["x/y", "-y/x", "y/x", "-x/y"], Answer: 1
   - Example 5: "The length of latus rectum of the parabola 4y^2 + 3x + 3y + 1 = 0 is:" Options: ["4/3", "7", "12", "3/4"], Answer: 3
   - Example 6: "If xy = e^(x-y), then dy/dx is equal to:" Options: ["log(x)/log(x-y)", "e^x/x(x-y)", "log(x)/(1+log(x))^2", "1/y - 1/(x-y)"], Answer: 2

RULES:
- Generate EXACTLY 20 MCQ questions
- Each question must have exactly 4 options
- Base questions ONLY on topics from the source content above
- Do NOT repeat any question from the used list
- ans must be the integer index of the correct option (0, 1, 2, or 3)
- Each question is worth 1 mark

Output ONLY a valid JSON array of exactly 20 items. Each item:
{{"q":"question text","type":"MCQ","topic":"topic name","opts":["option A","option B","option C","option D"],"ans":0,"marks":1}}"""

    try:
        client = get_groq_client()
        resp = create_chat_completion_with_fallback(
            client=client,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096,
        )
        questions = parse_llm_json(resp.choices[0].message.content)
    except GroqAPIKeyError:
        # Re-raise key errors so the generate endpoint can surface them clearly
        raise
    except Exception as exc:
        exc_str = str(exc).lower()
        # Detect authentication errors and re-raise with a clear message
        if "invalid_api_key" in exc_str or "authentication" in exc_str or "401" in exc_str:
            raise GroqAPIKeyError(
                f"Groq API key is invalid or expired. Error: {exc}. "
                "Get a new key from https://console.groq.com/keys and update backend/.env"
            ) from exc
        logger.error("Error calling Groq API: %s", exc)
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    valid_questions: List[dict] = []
    for q in questions:
        if not isinstance(q, dict) or "q" not in q or "opts" not in q or "ans" not in q:
            continue
        q["id"] = f"{set_label}-{len(valid_questions)}"
        q["type"] = q.get("type", "MCQ")
        q["marks"] = q.get("marks", 1)
        used_questions.add(q.get("q", ""))
        valid_questions.append(q)
    return valid_questions[:20]


def detect_subject(sample_text: str) -> Optional[str]:
    """Ask Groq to label a small text sample with a subject name.

    Returns ``None`` on any failure so callers can fall back to a default.
    """

    try:
        client = get_groq_client()
        resp = create_chat_completion_with_fallback(
            client=client,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "What subject is this exam paper about? Reply with just the "
                        f"subject name, nothing else.\n{sample_text[:500]}"
                    ),
                }
            ],
            temperature=0.1,
            max_tokens=20,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def generate_kcet_mcqs_from_textbook(
    context_chunks: Iterable[str],
    subject: str,
    set_label: str,
    used_questions: Set[str],
    questions_needed: int = 20,
    chapter_names: Optional[List[str]] = None,
) -> List[dict]:
    """Generate KCET-level MCQs from textbook content chunks.

    Reads actual extracted textbook text and creates high-quality KCET-pattern
    MCQs matching the difficulty and style of KCET exams.
    """

    chunks = list(context_chunks)
    # The caller already passes one big context string; join them just in case
    context = "\n\n".join(chunks)
    # Trim if needed to keep within token limits
    if len(context) > 14000:
        context = context[:14000]

    used_str = (
        "\n".join(f"- {q}" for q in list(used_questions)[:30])
        if used_questions
        else "None"
    )

    chapters_str = ""
    if chapter_names:
        chapters_str = f"\nChapters covered: {', '.join(chapter_names)}\n"

    prompt = f"""You are an expert KCET (Karnataka Common Entrance Test) question paper setter for {subject}.
{chapters_str}
Use ONLY the following textbook content to create exactly {questions_needed} KCET-level MCQ questions:

--- TEXTBOOK CONTENT START ---
{context}
--- TEXTBOOK CONTENT END ---

Questions already used in other sets (DO NOT repeat any of these):
{used_str}

STRICT KCET EXAM RULES:
1. NO TRIVIAL/FACTUAL DEFINITIONS: Do NOT ask simple fact-retrieval questions (e.g. 'What is the main objective of...', 'Who discovered...', 'Define the term...').
2. HIGH-QUALITY PROBLEMS: Every question must be a problem-solving, calculation, application-based, or rigorous conceptual deduction question.
3. SUBJECT-SPECIFIC STANDARDS:
   - Mathematics: Focus on calculation-heavy problems (e.g., calculus/derivatives/integrals, limits, matrix order/determinant properties, vector dot/cross products, trigonometry simplifications, relations/functions/mappings). Use mathematical equations and variables in the question stem.
   - Physics: Formulate numerical problems applying physics formulas (e.g., electrostatics, circuit dynamics, mechanics, thermodynamics, wave optics). 
   - Chemistry: Include stoichiometry calculations, organic reactions (reagents, products), physical chemistry numericals (kinetics, chemical equilibrium), electronic configurations.
   - Biology: Focus on deep understanding, genetic crosses (Mendelian ratios), physiological mechanisms, cellular stages.
4. STYLE & CONCISENESS: Keep the question stem brief, precise, and containing clear mathematical/scientific conditions.
5. MATHEMATICAL EXAMPLES (Use this style for Mathematics):
   - Example 1: "If Set A has 4 elements and set B has 5 elements, then the number of injective mappings that can be defined from A to B is:" Options: ["144", "72", "60", "120"], Answer: 3
   - Example 2: "The value of sin^-1(cos(53*pi/5)) is:" Options: ["3*pi/5", "-3*pi/5", "pi/10", "-pi/10"], Answer: 3
   - Example 3: "If A is any square matrix of order 3x3, then |3A| is equal to:" Options: ["3|A|", "1/3|A|", "27|A|", "9|A|"], Answer: 2
   - Example 4: "If y = e^(sin^-1(t^2-1)) and x = e^(sec^-1(1/(t^2-1))), then dy/dx is equal to:" Options: ["x/y", "-y/x", "y/x", "-x/y"], Answer: 1
   - Example 5: "The length of latus rectum of the parabola 4y^2 + 3x + 3y + 1 = 0 is:" Options: ["4/3", "7", "12", "3/4"], Answer: 3
   - Example 6: "If xy = e^(x-y), then dy/dx is equal to:" Options: ["log(x)/log(x-y)", "e^x/x(x-y)", "log(x)/(1+log(x))^2", "1/y - 1/(x-y)"], Answer: 2

STRICT OUTPUT RULES:
- Generate EXACTLY {questions_needed} multiple choice questions — no more, no less
- Every question MUST have EXACTLY 4 options (A, B, C, D)
- Base EVERY question STRICTLY on the textbook content provided above — do NOT invent facts
- ans must be the 0-based index of the CORRECT option (0=A, 1=B, 2=C, 3=D)
- Each question is worth 1 mark (KCET standard)
- Do NOT repeat any question from the "already used" list

Output ONLY a valid JSON array of exactly {questions_needed} objects. No markdown, no explanation, ONLY the JSON array.
Each object MUST follow this exact format:
{{"q":"question text","type":"MCQ","topic":"specific topic/chapter name","opts":["option A","option B","option C","option D"],"ans":0,"marks":1}}"""

    try:
        client = get_groq_client()
        resp = create_chat_completion_with_fallback(
            client=client,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=6000,
        )
        questions = parse_llm_json(resp.choices[0].message.content)
    except GroqAPIKeyError:
        raise
    except Exception as exc:
        exc_str = str(exc).lower()
        if "invalid_api_key" in exc_str or "authentication" in exc_str or "401" in exc_str:
            raise GroqAPIKeyError(
                f"Groq API key is invalid or expired. Error: {exc}. "
                "Get a new key from https://console.groq.com/keys and update backend/.env"
            ) from exc
        logger.error("Error calling Groq API for textbook generation: %s", exc)
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    valid_questions: List[dict] = []
    for q in questions:
        if not isinstance(q, dict) or "q" not in q or "opts" not in q or "ans" not in q:
            continue
        if not isinstance(q.get("opts"), list) or len(q["opts"]) != 4:
            continue
        q["id"] = f"{set_label}-{len(valid_questions)}"
        q["type"] = "MCQ"
        q["marks"] = 1
        used_questions.add(q.get("q", ""))
        valid_questions.append(q)

    logger.info(
        "Textbook KCET generation: set %s → %d/%d valid questions",
        set_label, len(valid_questions), questions_needed,
    )
    return valid_questions[:questions_needed]
