import enum as _enum
import typing as _typing

from pydantic import BaseModel

ApiEnv = _typing.Literal["prod", "dev", "local", "docker"]


class BaseUrl(_enum.StrEnum):
    """The base URL to connect to the API."""

    PROD = "https://api.crypticorn.com"
    DEV = "https://api.crypticorn.dev"
    LOCAL = "http://localhost"
    DOCKER = "http://host.docker.internal"

    @classmethod
    def from_env(cls, env: ApiEnv) -> "BaseUrl":
        """Load the base URL from the API environment."""
        if env == "prod":
            return cls.PROD
        elif env == "dev":
            return cls.DEV
        elif env == "local":
            return cls.LOCAL
        elif env == "docker":
            return cls.DOCKER


class ErrorResponse(BaseModel):
    """
    Error response schema.
    """

    detail: str


error_response = {
    "default": {
        "model": ErrorResponse,
        "description": "Error response",
    },
}
"""
Error response schema openapi definition.
"""
