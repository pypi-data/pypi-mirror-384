import re
from typing import Any, Optional, TypeVar
from uuid import uuid4

from httpx import Headers


def build_url(*url_components: Optional[str]) -> str:
    """
    Builds a URL from the provided components, removing any unintended extra slashes and ignoring
    components that are None.
    """
    compacted_url_components = [
        component for component in url_components if component is not None
    ]
    components_joined_by_slash = "/".join(compacted_url_components)

    url = _remove_double_slashes_not_preceded_by_columns(components_joined_by_slash)

    return url


def _remove_double_slashes_not_preceded_by_columns(url: str) -> str:
    if url.startswith("https:"):
        return re.sub(r"(?<!https:)/+", "/", url)
    elif url.startswith("http:"):
        return re.sub(r"(?<!http:)/+", "/", url)


T = TypeVar("T")


def get_all_missing_keys_in_dict(dict_: dict[T, Any], keys: list[T]) -> list[T]:
    """Returns a list of keys that are missing from the provided dictionary."""
    missing_keys = [key for key in keys if key not in dict_]
    return missing_keys

def mask_str(string: str, keep: int = 4) -> str:
    """
    Mask all but the last `keep` characters of a str.
    Example: abcdefghijkl -> ********ijkl
    """
    if len(string) <= keep:
        return "*" * len(string)
    masked = "*" * (len(string) - keep) + string[-keep:]
    return masked

def create_short_unique_id(length: int = 12) -> str:
    return uuid4().hex[:length]

def obfuscate_headers(headers: Headers | dict[str, str]) -> dict[str, str]:
    """
    Return a copy of headers with sensitive values partially obfuscated.
    Sensitive fields are detected by common HTTP header naming conventions.
    """
    obfuscated = {}

    for key, value in headers.items():
        lower_key = key.lower()

        is_sensitive_header = (
            any(  # Check if the header key contains any of the sensitive keywords
                sensitive in lower_key
                for sensitive in [
                    "authorization",
                    "api-key",
                    "apikey",
                    "secret",
                    "token",
                    "password",
                    "passwd",
                ]
            )
        )

        if is_sensitive_header:
            obfuscated[key] = mask_str(value)

        else:
            obfuscated[key] = value

    return obfuscated
