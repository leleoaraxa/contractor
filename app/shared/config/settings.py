# app/shared/config/settings.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    runtime_host: str = "0.0.0.0"
    runtime_port: int = 8000

    control_host: str = "0.0.0.0"
    control_port: int = 8001

    # Local registry base for MVP (filesystem). In AWS stage, this will be S3.
    bundle_registry_base: str = "registry/tenants"
    control_base_url: str = "http://localhost:8001"
    control_alias_store_path: str = "registry/control_plane/tenant_aliases.json"
    control_quality_report_base: str = "registry/control_plane/quality_reports"
    control_promotion_set_base: str = "registry/control_plane/promotion_sets"


settings = Settings()
