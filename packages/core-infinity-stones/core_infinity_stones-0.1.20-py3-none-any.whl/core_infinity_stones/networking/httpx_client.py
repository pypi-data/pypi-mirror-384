from enum import StrEnum
from typing import Any, Callable, Coroutine, Mapping, Optional

from httpx import URL, AsyncBaseTransport, AsyncClient, Request, Response
from httpx._client import EventHook
from httpx._config import (
    DEFAULT_LIMITS,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_TIMEOUT_CONFIG,
    Limits,
)
from httpx._types import (
    AuthTypes,
    CertTypes,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    TimeoutTypes,
)

from core_infinity_stones.core.utils.helpers import obfuscate_headers
from core_infinity_stones.logging import (
    IncomingResponseEvent,
    Logger,
    OutgoingRequestEvent,
)



class LoggingVerbosity(StrEnum):
    NONE = "NONE"
    """Do not log anything."""

    LOW = "LOW"
    """Only log request and response metadata (method, URL, status code, duration)."""

    MEDIUM = "MEDIUM"
    """Log request and response headers in addition to metadata."""

    HIGH = "HIGH"
    """Log request and response bodies truncated to a 1000 chars in addition to metadata and headers."""

    FULL = "FULL"
    """Log request and response full bodies in addition to metadata and headers."""

    @staticmethod
    def form_string(string: str) -> "LoggingVerbosity":
        try:
            return LoggingVerbosity[string.upper()]
        except KeyError:
            return LoggingVerbosity.NONE

    @property
    def should_log_headers(self) -> bool:
        return self in {LoggingVerbosity.MEDIUM, LoggingVerbosity.HIGH, LoggingVerbosity.FULL}

    @property
    def should_log_body(self) -> bool:
        return self in {LoggingVerbosity.HIGH, LoggingVerbosity.FULL}

    @property
    def should_truncate_body(self) -> bool:
        return self != LoggingVerbosity.FULL


class HttpxClientWithLogging(AsyncClient):
    def __init__(
        self,
        logger: Logger,
        auth: AuthTypes | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        cert: CertTypes | None = None,
        http1: bool = True,
        http2: bool = False,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
        follow_redirects: bool = False,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: None | (Mapping[str, list[EventHook]]) = None,
        base_url: URL | str = "",
        transport: AsyncBaseTransport | None = None,
        trust_env: bool = True,
        default_encoding: str | Callable[[bytes], str] = "utf-8",
        request_verbosity_level: LoggingVerbosity = LoggingVerbosity.HIGH,
        response_verbosity_level: LoggingVerbosity = LoggingVerbosity.HIGH,
        path_to_request_verbosity_level_map: Optional[Mapping[str, LoggingVerbosity]] = None,
        path_to_response_verbosity_level_map: Optional[Mapping[str, LoggingVerbosity]] = None,
    ) -> None:
        event_hooks_with_logging: Optional[Mapping[str, list[Callable[..., Any]]]] = None

        request_event_hooks = event_hooks.get("request", []) if event_hooks else []
        response_event_hooks = event_hooks.get("response", []) if event_hooks else []

        request_logger = self.create_request_logger(
            request_verbosity_level, path_to_request_verbosity_level_map, logger
        )

        response_logger = self.create_response_logger(
            response_verbosity_level, path_to_response_verbosity_level_map, logger
        )

        event_hooks_with_logging = {
            "request": [request_logger, *request_event_hooks],
            "response": [response_logger, *response_event_hooks],
        }

        super().__init__(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            cert=cert,
            http1=http1,
            http2=http2,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks_with_logging or event_hooks,
            base_url=base_url,
            transport=transport,
            trust_env=trust_env,
            default_encoding=default_encoding,
        )

    def create_request_logger(
        self,
        default_verbosity_level: LoggingVerbosity,
        path_to_verbosity_level_map: Optional[Mapping[str, LoggingVerbosity]],
        logger: Logger,
    ) -> Callable[[Request], Coroutine[Any, Any, None]]:
        async def request_logger(request: Request) -> None:
            verbosity = ( 
                path_to_verbosity_level_map.get(request.url.path, default_verbosity_level)
                if path_to_verbosity_level_map
                else default_verbosity_level
            )

            if verbosity == LoggingVerbosity.NONE:
                return

            request_body = None

            if request.content and verbosity.should_log_body:
                request_body = (
                    request.content[:1000] + bytes("... [truncated]", "utf-8")
                    if verbosity.should_truncate_body and len(request.content) > 1000
                    else request.content
                )

            headers = (
                obfuscate_headers(request.headers)
                if verbosity.should_log_headers
                else None
            )

            logger.info(
                OutgoingRequestEvent(
                    method=request.method,
                    url=str(request.url),
                    headers=headers,
                    body=request_body,
                    verbosity_level=verbosity,
                )
            )

        return request_logger

    def create_response_logger(
        self,
        default_verbosity_level: LoggingVerbosity,
        path_to_verbosity_level_map: Optional[Mapping[str, LoggingVerbosity]],
        logger: Logger,
    ) -> Callable[[Response], Coroutine[Any, Any, None]]:

        async def response_logger(response: Response) -> None:
            verbosity = (
                path_to_verbosity_level_map.get(response.request.url.path, default_verbosity_level)
                if path_to_verbosity_level_map
                else default_verbosity_level
            )

            if verbosity == LoggingVerbosity.NONE:
                return

            await response.aread()  # Ensure the response content is read
            request = response.request
            response_body = None

            if verbosity.should_log_body:
                response_body = (
                    response.text[:1000]
                    if verbosity.should_truncate_body
                    else response.text
                )

            headers = (
                obfuscate_headers(response.headers)
                if verbosity.should_log_headers
                else None
            )

            logger.info(
                IncomingResponseEvent(
                    method=request.method,
                    url=str(request.url),
                    status_code=response.status_code,
                    duration_ms=response.elapsed.total_seconds() * 1000,
                    headers=headers,
                    body=response_body,
                    verbosity_level=verbosity,
                )
            )

        return response_logger
