# app/control_plane/domain/audit/logger.py
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.shared.config.settings import settings
from app.shared.logging.redact import redact_obj

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Minimal JSONL audit logger. Stores only non-sensitive metadata.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.control_audit_log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: Dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "action": event,
            **payload,
        }
        safe_record = redact_obj(record)
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(safe_record, ensure_ascii=False) + "\n")
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("audit log write failed: %s", exc)
