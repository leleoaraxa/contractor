# app/shared/logging/redact.py
from __future__ import annotations

import re
from typing import Any, Dict

# Minimal baseline redaction. Extend via policies later.
_PATTERNS = [
    (
        re.compile(
            r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*([^\s,;]+)"
        ),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"(?i)Authorization:\s*Bearer\s+([^\s]+)"),
        r"Authorization: Bearer [REDACTED]",
    ),
]


def redact_text(text: str) -> str:
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]
    return obj


def redact_log_record(record: Dict[str, Any]) -> Dict[str, Any]:
    # Apply conservative redaction to all string fields
    return redact_obj(record)
