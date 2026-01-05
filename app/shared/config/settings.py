# app/shared/config/settings.py
from __future__ import annotations

import json
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_parse_delimiter=",",  # <-- CRÍTICO: list[str] aceita "dev-key" e "k1,k2"
    )

    environment: str = "local"
    log_level: str = "INFO"

    # Accept env as:
    # - "dev-key"
    # - "k1,k2"
    # - '["k1","k2"]'
    contractor_api_keys: list[str] | str | None = Field(
        default_factory=list, validation_alias="CONTRACTOR_API_KEYS"
    )

    contractor_auth_disabled: bool = Field(
        default=False, validation_alias="CONTRACTOR_AUTH_DISABLED"
    )

    runtime_host: str = "0.0.0.0"
    runtime_port: int = 8000

    control_host: str = "0.0.0.0"
    control_port: int = 8001

    runtime_redis_url: str | None = None
    rate_limit_redis_url: str | None = None

    # Local registry base for MVP (filesystem). In AWS stage, this will be S3.
    bundle_registry_base: str = "registry/tenants"
    control_base_url: str = "http://localhost:8001"
    control_alias_store_path: str = "registry/control_plane/tenant_aliases.json"
    control_quality_report_base: str = "registry/control_plane/quality_reports"
    control_promotion_set_base: str = "registry/control_plane/promotion_sets"
    control_audit_log_path: str = "registry/control_plane/audit.log"

    rate_limit_rps: int = 10
    rate_limit_burst: int = 20

    @field_validator("contractor_api_keys", mode="before")
    @classmethod
    def _parse_contractor_api_keys(cls, v):
        """
        Allow CONTRACTOR_API_KEYS to be provided as:
          - a single string: "dev-key"
          - CSV string: "k1,k2"
          - JSON list string: '["k1","k2"]'
          - list[str] (already parsed)
        """
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(x).strip() for x in arr if str(x).strip()]
                except Exception:
                    # fall back to CSV parsing below
                    pass
            # CSV or single token
            return [p.strip() for p in s.split(",") if p.strip()]
        # last-resort
        s = str(v).strip()
        return [s] if s else []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        def contractor_env_settings():
            data = {}
            api_keys = os.getenv("CONTRACTOR_API_KEYS")
            if api_keys is not None:
                data["contractor_api_keys"] = api_keys
            auth_disabled = os.getenv("CONTRACTOR_AUTH_DISABLED")
            if auth_disabled is not None:
                data["contractor_auth_disabled"] = auth_disabled
            return data

        return (
            contractor_env_settings,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()
