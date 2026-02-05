from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_CONFIG_PATH = REPO_ROOT / "data" / "audit" / "audit.yaml"
AUDIT_CONFIG_ENV_JSON = "CONTRACTOR_AUDIT_CONFIG_JSON"
AUDIT_CONFIG_ENV_PATH = "CONTRACTOR_AUDIT_CONFIG_PATH"


class AuditConfigError(RuntimeError):
    """Raised when audit config is missing/invalid while auditing is required."""


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_utc_iso() -> str:
    return now_utc().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc_yyyymmdd() -> str:
    return now_utc().strftime("%Y-%m-%d")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_config_from_path(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise AuditConfigError("Audit config invalid")
    return data


def validate_audit_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise AuditConfigError("Audit config invalid")

    enabled = config.get("enabled")
    sink = config.get("sink")
    file_path = config.get("file_path")
    retention_days = config.get("retention_days")

    if not isinstance(enabled, bool):
        raise AuditConfigError("Audit config invalid")
    if sink not in {"stdout", "file"}:
        raise AuditConfigError("Audit config invalid")
    if not isinstance(file_path, str) or not file_path.strip():
        raise AuditConfigError("Audit config invalid")
    if not isinstance(retention_days, int) or retention_days < 1:
        raise AuditConfigError("Audit config invalid")

    return {
        "enabled": enabled,
        "sink": sink,
        "file_path": file_path,
        "retention_days": retention_days,
    }


def load_audit_config() -> dict[str, Any]:
    env_json = os.getenv(AUDIT_CONFIG_ENV_JSON)
    if env_json:
        try:
            return validate_audit_config(json.loads(env_json))
        except (json.JSONDecodeError, AuditConfigError) as exc:
            raise AuditConfigError("Audit config invalid") from exc

    env_path = os.getenv(AUDIT_CONFIG_ENV_PATH)
    config_path = Path(env_path) if env_path else DEFAULT_AUDIT_CONFIG_PATH
    try:
        return validate_audit_config(_load_config_from_path(config_path))
    except FileNotFoundError as exc:
        raise AuditConfigError("Audit config missing") from exc
    except (json.JSONDecodeError, yaml.YAMLError, AuditConfigError) as exc:
        raise AuditConfigError("Audit config invalid") from exc


def _resolve_rotated_path(file_path: str, event_day: str) -> Path:
    base_path = Path(file_path)
    if str(base_path).endswith(".log.jsonl"):
        rotated_name = f"{base_path.name[:-10]}-{event_day}.log.jsonl"
    else:
        rotated_name = f"{base_path.stem}-{event_day}{base_path.suffix or '.log.jsonl'}"
    return base_path.with_name(rotated_name)


def _cleanup_retention(rotated_path: Path, retention_days: int, today_utc: datetime) -> None:
    parent = rotated_path.parent
    prefix = rotated_path.name.split("-")[0] + "-"
    cutoff_date = (today_utc - timedelta(days=retention_days)).date()
    for path in parent.glob(f"{prefix}*.log.jsonl"):
        name = path.name
        if not name.startswith(prefix) or not name.endswith(".log.jsonl"):
            continue
        date_part = name[len(prefix) : -10]
        try:
            file_date = datetime.strptime(date_part, "%Y-%m-%d").date()
        except ValueError:
            continue
        if file_date < cutoff_date:
            path.unlink(missing_ok=True)


def audit_emit(event_dict: dict[str, Any]) -> None:
    config = load_audit_config()
    if not config["enabled"]:
        return

    line = json.dumps(event_dict, ensure_ascii=False)
    if config["sink"] == "stdout":
        print(line)
        return

    event_day = str(event_dict.get("ts_utc", ""))[:10]
    if len(event_day) != 10:
        event_day = today_utc_yyyymmdd()
    rotated_path = _resolve_rotated_path(config["file_path"], event_day)
    rotated_path.parent.mkdir(parents=True, exist_ok=True)

    _cleanup_retention(rotated_path, config["retention_days"], now_utc())
    try:
        with rotated_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
    except OSError as exc:
        raise AuditConfigError("Audit sink write failure") from exc
