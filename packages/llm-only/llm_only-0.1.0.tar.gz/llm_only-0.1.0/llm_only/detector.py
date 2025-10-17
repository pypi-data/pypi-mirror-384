import re
from typing import Optional

LLM_PATTERNS = [
    re.compile(r"OpenAI", re.I),
    re.compile(r"GPT", re.I),
    re.compile(r"Claude", re.I),
    re.compile(r"Perplexity", re.I),
    re.compile(r"Google-Extended", re.I),
    re.compile(r"Bard", re.I),
]

def is_llm_request(user_agent: Optional[str] = None, headers: Optional[dict] = None) -> bool:
    if headers and headers.get("x-llm-preview", "").lower() == "1":
        return True
    if not user_agent:
        return False
    return any(p.search(user_agent) for p in LLM_PATTERNS)
