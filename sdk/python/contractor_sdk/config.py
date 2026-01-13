from dataclasses import dataclass


@dataclass(frozen=True)
class SDKConfig:
    base_url: str
    api_key: str
    timeout: float = 30.0

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")
