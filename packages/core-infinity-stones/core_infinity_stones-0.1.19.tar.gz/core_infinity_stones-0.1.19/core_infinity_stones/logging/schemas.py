from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from core_infinity_stones.core.utils.helpers import create_short_unique_id
from core_infinity_stones.errors.base_error import LocalizedMessage, Severity


class RequestDetails(BaseModel):
    path: Optional[str] = None
    method: Optional[str] = None
    query_params: Optional[dict[str, str]] = None
    user_agent: Optional[str] = None

class LoggerContext(BaseModel):
    trace_id: str
    request_details: "RequestDetails"
    context_metadata: dict[str, Any]
    topics: set[str]

class EventLevel(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: create_short_unique_id())
    code: str
    message: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    topic: Optional[str] = None


class EventWithTracesDetails(BaseModel):
    id: str
    trace_id: str
    level: EventLevel
    path: Optional[str] = None
    method: Optional[str] = None
    query_params: Optional[dict[str, Any]] = None
    user_agent: Optional[str] = None
    code: str
    topics: Optional[set[str]] = None
    message: Optional[str] = None
    context_metadata: Optional[dict[str, Any]] = None
    details: Optional[dict[str, Any]] = None
    sampling_percentage: int
    timestamp: str

    @classmethod
    def from_event(
        cls,
        event: Event,
        trace_id: str,
        level: EventLevel,
        sampling_percentage: int,
        context_metadata: dict[str, Any],
        topics: set[str],
        request_details: Optional[RequestDetails] = None,
    ) -> "EventWithTracesDetails":
        event_topics = topics.copy()

        if event.topic:
            event_topics.add(event.topic)

        return EventWithTracesDetails(
            id=event.id,
            trace_id=trace_id,
            level=level,
            path=request_details.path if request_details else None,
            method=request_details.method if request_details else None,
            query_params=request_details.query_params if request_details else None,
            user_agent=request_details.user_agent if request_details else None,
            code=event.code,
            topics=event_topics if event_topics else None,
            message=event.message,
            context_metadata=context_metadata if context_metadata else None,
            details=event.details,
            sampling_percentage=sampling_percentage,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )


class ErrorEvent(BaseModel):
    id: str
    trace_id: str
    level: EventLevel
    path: Optional[str] = None
    method: Optional[str] = None
    query_params: Optional[dict[str, Any]] = None
    user_agent: Optional[str] = None
    severity: Severity
    code: str
    topics: Optional[set[str]] = None
    message: str
    context_metadata: Optional[dict[str, Any]] = None
    details: Optional[dict[str, Any]] = None
    occurred_while: Optional[str] = None
    caused_by: Optional[dict[str, Any]] = None
    status_code: int
    public_code: str
    public_message: LocalizedMessage
    public_details: Optional[dict[str, Any]] = None
    sampling_percentage: int
    timestamp: str


# Common Events

class IncomingRequestEvent(Event):
    def __init__(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        details = {
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
        }

        super().__init__(code="INCOMING_REQUEST", details=details)


class OutgoingRequestEvent(Event):
    def __init__(
        self,
        verbosity_level: str,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        details = {
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "verbosity_level": verbosity_level,
        }

        super().__init__(code="OUTGOING_REQUEST", details=details)


class OutgoingResponseEvent(Event):
    def __init__(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        details = {
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "headers": headers,
            "body": body,
        }

        super().__init__(code="OUTGOING_RESPONSE", details=details)


class IncomingResponseEvent(Event):
    def __init__(
        self,
        verbosity_level: str,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        headers: Optional[dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        details = {
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "headers": headers,
            "body": body,
            "verbosity_level": verbosity_level,
        }

        super().__init__(code="INCOMING_RESPONSE", details=details)