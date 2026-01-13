class APIError(Exception):
    """Base error for SDK HTTP interactions."""

    def __init__(self, message: str, status_code: int | None = None, payload: object | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class ClientError(APIError):
    """Represents 4xx errors."""


class ServerError(APIError):
    """Represents 5xx errors."""
