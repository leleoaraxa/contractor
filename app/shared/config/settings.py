# app/shared/config/settings.py
from __future__ import annotations

import json
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource


def _normalize_api_keys(v):
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
        return [p.strip() for p in s.split(",") if p.strip()]
    s = str(v).strip()
    return [s] if s else []


def _normalize_tenant_residency_requirements(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        normalized = {}
        for key, region in value.items():
            tenant_id = str(key).strip()
            region_value = str(region).strip()
            if tenant_id and region_value:
                normalized[tenant_id] = region_value
        return normalized
    if isinstance(value, list):
        normalized = {}
        for item in value:
            if isinstance(item, str):
                entry = item.strip()
                if not entry or "=" not in entry:
                    continue
                tenant_id, region = entry.split("=", 1)
                tenant_id = tenant_id.strip()
                region = region.strip()
                if tenant_id and region:
                    normalized[tenant_id] = region
        return normalized
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        if raw.startswith("{"):
            try:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    return _normalize_tenant_residency_requirements(payload)
            except Exception:
                pass
        normalized = {}
        for entry in raw.split(","):
            entry = entry.strip()
            if not entry or "=" not in entry:
                continue
            tenant_id, region = entry.split("=", 1)
            tenant_id = tenant_id.strip()
            region = region.strip()
            if tenant_id and region:
                normalized[tenant_id] = region
        return normalized
    return {}


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
    contractor_api_keys: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("CONTRACTOR_API_KEYS", "CONTRACTOR_API_KEY"),
    )

    contractor_auth_disabled: bool = Field(
        default=False, validation_alias="CONTRACTOR_AUTH_DISABLED"
    )

    runtime_host: str = "0.0.0.0"
    runtime_port: int = 8000
    runtime_base_url: str | None = Field(default=None, validation_alias="RUNTIME_BASE_URL")

    control_host: str = "0.0.0.0"
    control_port: int = 8001

    runtime_redis_url: str | None = None
    rate_limit_redis_url: str | None = None
    runtime_async_enabled: bool = Field(default=False, validation_alias="RUNTIME_ASYNC_ENABLED")
    runtime_async_always: bool = Field(
        default=False,
        validation_alias=AliasChoices("RUNTIME_ASYNC_ALWAYS", "ASYNC_ALWAYS"),
    )
    runtime_async_question_length_threshold: int = Field(
        default=200, validation_alias="RUNTIME_ASYNC_QUESTION_LENGTH_THRESHOLD"
    )
    runtime_async_result_ttl_seconds: int = Field(
        default=600, validation_alias="RUNTIME_ASYNC_RESULT_TTL_SECONDS"
    )
    runtime_async_worker_block_seconds: int = Field(
        default=5, validation_alias="RUNTIME_ASYNC_WORKER_BLOCK_SECONDS"
    )
    runtime_dedicated_tenant_id: str | None = Field(
        default=None, validation_alias="RUNTIME_DEDICATED_TENANT_ID"
    )
    runtime_region: str | None = Field(default=None, validation_alias="RUNTIME_REGION")
    runtime_tenant_residency_requirements: dict[str, str] = Field(
        default_factory=dict,
        validation_alias="RUNTIME_TENANT_RESIDENCY_REQUIREMENTS",
    )

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
        return _normalize_api_keys(v)

    @field_validator("runtime_tenant_residency_requirements", mode="before")
    @classmethod
    def _parse_runtime_tenant_residency_requirements(cls, v):
        """
        Allow RUNTIME_TENANT_RESIDENCY_REQUIREMENTS to be provided as:
          - CSV string: "tenant-a=sa-east-1,tenant-b=us-east-1"
          - JSON dict string: '{"tenant-a":"sa-east-1"}'
          - list[str] entries: ["tenant-a=sa-east-1"]
          - dict[str, str] (already parsed)
        """
        return _normalize_tenant_residency_requirements(v)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        class ContractorEnvSettingsSource(EnvSettingsSource):
            def prepare_field_value(self, field_name, field, field_value, value_is_complex):
                try:
                    return super().prepare_field_value(
                        field_name, field, field_value, value_is_complex
                    )
                except ValueError:
                    if field_name in {
                        "contractor_api_keys",
                        "runtime_tenant_residency_requirements",
                    }:
                        return field_value
                    raise

        class ContractorDotEnvSettingsSource(DotEnvSettingsSource):
            def prepare_field_value(self, field_name, field, field_value, value_is_complex):
                try:
                    return super().prepare_field_value(
                        field_name, field, field_value, value_is_complex
                    )
                except ValueError:
                    if field_name in {
                        "contractor_api_keys",
                        "runtime_tenant_residency_requirements",
                    }:
                        return field_value
                    raise

        contractor_env = ContractorEnvSettingsSource(
            settings_cls,
            env_settings.case_sensitive,
            env_settings.env_prefix,
            env_settings.env_nested_delimiter,
            env_settings.env_nested_max_split,
            env_settings.env_ignore_empty,
            env_settings.env_parse_none_str,
            env_settings.env_parse_enums,
        )

        contractor_dotenv = ContractorDotEnvSettingsSource(
            settings_cls,
            dotenv_settings.env_file,
            dotenv_settings.env_file_encoding,
            dotenv_settings.case_sensitive,
            dotenv_settings.env_prefix,
            dotenv_settings.env_nested_delimiter,
            dotenv_settings.env_nested_max_split,
            dotenv_settings.env_ignore_empty,
            dotenv_settings.env_parse_none_str,
            dotenv_settings.env_parse_enums,
        )

        return (init_settings, contractor_env, contractor_dotenv, file_secret_settings)


settings = Settings()
