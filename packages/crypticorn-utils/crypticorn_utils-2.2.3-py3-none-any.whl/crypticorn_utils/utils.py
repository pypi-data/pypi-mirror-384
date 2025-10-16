"""General utility functions and helper methods used across the codebase."""

import datetime as _datetime
import secrets as _secrets
import string as _string
import typing as _typing


def gen_random_id(length: int = 20) -> str:
    """Generate a random base62 string (a-zA-Z0-9) of specified length. The max possible combinations is 62^length.
    Kucoin max 40, bingx max 40"""
    charset = _string.ascii_letters + _string.digits
    return "".join(_secrets.choice(charset) for _ in range(length))


def optional_import(module_name: str, extra_name: str) -> _typing.Any:
    """
    Tries to import a module. Raises `ImportError` if not found with a message to install the extra dependency.
    """
    try:
        return __import__(module_name)
    except ImportError as e:
        raise ImportError(
            f"Optional dependency '{module_name}' is required for this feature. "
            f"Install it with: pip install crypticorn[{extra_name}]"
        ) from e


def datetime_to_timestamp(v: _typing.Any):
    """Converts a datetime to a timestamp.
    Can be used as a pydantic validator.
    >>> from pydantic import BeforeValidator, BaseModel
    >>> class MyModel(BaseModel):
    ...     timestamp: Annotated[int, BeforeValidator(datetime_to_timestamp)]
    """
    if isinstance(v, list):
        return [
            int(item.timestamp()) if isinstance(item, _datetime.datetime) else item
            for item in v
        ]
    elif isinstance(v, _datetime.datetime):
        return int(v.timestamp())
    return v
