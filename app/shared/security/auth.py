from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.shared.config.settings import settings


def _normalized_keys() -> set[str]:
    raw = settings.contractor_api_keys or []
    return {str(k).strip() for k in raw if str(k).strip()}


def auth_disabled() -> bool:
    return bool(settings.contractor_auth_disabled)


def require_api_key(request: Request) -> None:
    if auth_disabled():
        return

    allowed_keys = _normalized_keys()
    if not allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required: configure CONTRACTOR_API_KEYS",
        )

    provided = (request.headers.get("X-API-Key") or "").strip()
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing X-API-Key"
        )

    if provided not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid API key"
        )


def outbound_auth_headers() -> dict[str, str]:
    if auth_disabled():
        return {}

    allowed_keys = _normalized_keys()
    if not allowed_keys:
        return {}
    # deterministic selection of the first key
    key = sorted(allowed_keys)[0]
    return {"X-API-Key": key}
