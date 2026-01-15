# app/shared/logging/redact.py
from __future__ import annotations

import re
from typing import Any, Dict

# Minimal baseline redaction. Extend via policies later.
SENSITIVE_KEYS = {"question", "prompt", "content", "body", "payload"}

_PAYLOAD_PAIR_PATTERN = re.compile(
    r"(?i)(\"|')?(question|prompt|content|body|payload)(\"|')?\s*[:=]\s*([^,}\n]+)"
)

_PATTERNS = [
    (
        re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*([^\s,;]+)"),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"(?i)Authorization:\s*Bearer\s+([^\s]+)"),
        r"Authorization: Bearer [REDACTED]",
    ),
]


def redact_text(text: str) -> str:
    out = _PAYLOAD_PAIR_PATTERN.sub("[REDACTED]", text)
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        redacted: Dict[Any, Any] = {}
        for key, value in obj.items():
            if str(key).lower() in SENSITIVE_KEYS:
                continue
            redacted[key] = redact_obj(value)
        return redacted
    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]
    return obj


def redact_log_record(record: Dict[str, Any]) -> Dict[str, Any]:
    # Apply conservative redaction to all string fields
    return redact_obj(record)
