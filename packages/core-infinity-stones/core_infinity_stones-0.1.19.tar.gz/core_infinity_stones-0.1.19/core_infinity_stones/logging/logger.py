import random
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

from core_infinity_stones.errors.base_error import HttpError, Severity, UnexpectedError
from core_infinity_stones.logging.native_logger import create_json_logger
from core_infinity_stones.logging.schemas import (
    ErrorEvent,
    Event,
    EventLevel,
    EventWithTracesDetails,
    LoggerContext,
    RequestDetails,
)

logger_context: ContextVar[Optional[LoggerContext]] = ContextVar("logger_context", default=None)

class Logger:
    def __init__(
        self,
        event_codes_to_sampling_percentages_map: Optional[dict[str, int]] = None,
    ):
        """
        Initialize the Logger instance.

        Args:
            trace_id (str): The trace ID for the current request or context.

            logger (NativeLogger): The logger instance to use for logging events.

            request_details (Optional[RequestDetails]): Details about the request,
              such as path, method, and query parameters.

            context_metadata (dict[str, Any]): A dictionary to hold additional context metadata
                that will be included in every log entry.

            topics (set[str]): A set of topics associated with the logger instance.

            event_codes_to_sampling_percentages_map (Optional[dict[str, int]]): A mapping of event
                codes to their sampling percentages.
                This is a dictionary where keys are event codes and values are integers between 0 and 100,
                representing the probability of logging the specified event.
                If None, all events will be logged with 100% sampling.
                If an event code is not present in the map, it will default to 100% sampling.
        """
        self.logger = create_json_logger()
        self.event_codes_to_sampling_percentages_map = (
            event_codes_to_sampling_percentages_map
        )

    def set_logger_context(
        self,
        trace_id: str,
        request_details: RequestDetails,
        context_metadata: Optional[dict[str, Any]] = None,
        topics: Optional[set[str]] = None,
    ) -> None:
        logger_context.set(
            LoggerContext(
                trace_id=trace_id,
                request_details=request_details,
                context_metadata=context_metadata or {},
                topics=topics or set(),
            )
        )

    @property
    def trace_id(self) -> str:
        ctx = logger_context.get()

        if ctx is None:
            return ""

        return ctx.trace_id or ""

    @property
    def request_details(self) -> RequestDetails:
        ctx = logger_context.get()

        if ctx is None:
            return RequestDetails()

        return ctx.request_details

    @property
    def context_metadata(self) -> dict[str, Any]:
        ctx = logger_context.get()

        if ctx is None:
            return {}
        return ctx.context_metadata or {}

    @property
    def topics(self) -> set[str]:
        ctx = logger_context.get()

        if ctx is None:
            return set()
        return ctx.topics or set()

    def add_context_metadata(self, key: str, value: Any) -> None:
        ctx = logger_context.get()

        if ctx:
            ctx.context_metadata[key] = value
            logger_context.set(ctx)

    def remove_context_metadata(self, key: str) -> None:
        ctx = logger_context.get()

        if ctx:
            ctx.context_metadata.pop(key, None)
            logger_context.set(ctx)

    def add_topic(self, topic: str) -> None:
        ctx = logger_context.get()

        if ctx:
            ctx.topics.add(topic)
            logger_context.set(ctx)

    def remove_topic(self, topic: str) -> None:
        ctx = logger_context.get()

        if ctx:
            ctx.topics.discard(topic)
            logger_context.set(ctx)

    def info(
        self,
        event: Optional[Event] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        topic: Optional[str] = None
    ) -> None:
        if event is None:
            if code is None:
                return

            event = Event(code=code, message=message, details=details, topic=topic)

        self.log_event(event, logging_level=EventLevel.INFO)

    def warning(
        self,
        event: Optional[Event] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        topic: Optional[str] = None
    ) -> None:
        if event is None:
            if code is None:
                return

            event = Event(code=code, message=message, details=details, topic=topic)

        self.log_event(event, logging_level=EventLevel.WARNING)

    def error(
        self,
        error: Optional[HttpError | Exception] = None,
        id: Optional[str] = None,
        status_code: int = 500,
        severity: Severity = Severity.CRITICAL,
        topic: Optional[str] = None,
        debug_code: Optional[str] = None,
        debug_message: Optional[str] = None,
        occurred_while: Optional[str] = None,
        debug_details: dict[Any, Any] = {},
        caused_by: Optional[Exception] = None,
    ) -> None:
        if error is None:
            error = UnexpectedError(
                id=id,
                status_code=status_code,
                severity=severity,
                topic=topic,
                debug_code=debug_code,
                debug_message=debug_message,
                occurred_while=occurred_while,
                debug_details=debug_details,
                caused_by=caused_by,
            )

        if not isinstance(error, HttpError):
            error = UnexpectedError(
                caused_by=error,
            )

        event_code = error.debug_details.debug_code

        if not self._should_log_based_on_sampling_percentage(event_code):
            return

        error_event = self._format_error(error)

        self.logger.error(
            error.debug_details.debug_message, extra={"event": error_event}
        )

    def log_event(self, event: Event, logging_level: EventLevel) -> None:
        if not self._should_log_based_on_sampling_percentage(event.code):
            return

        sampling_percentage = (
            self.event_codes_to_sampling_percentages_map.get(event.code, 100)
            if self.event_codes_to_sampling_percentages_map
            else 100
        )

        event_with_tracing_details = EventWithTracesDetails.from_event(
            event,
            trace_id=self.trace_id,
            level=logging_level,
            sampling_percentage=sampling_percentage,
            context_metadata=self.context_metadata,
            topics=self.topics,
            request_details=self.request_details,
        )

        extra = {"event": event_with_tracing_details}

        if logging_level == EventLevel.INFO:
            self.logger.info(event.message, extra=extra)
        elif logging_level == EventLevel.WARNING:
            self.logger.warning(event.message, extra=extra)

    def _format_error(self, error: Optional[BaseException]) -> Optional[dict[str, Any]]:
        """
        Formats the error into a string representation.
        """
        if error is None:
            return None

        if isinstance(error, HttpError):
            event_code = error.debug_details.debug_code

            original_error_details = self._format_error(error.debug_details.caused_by)

            sampling_percentage = (
                self.event_codes_to_sampling_percentages_map.get(event_code, 100)
                if self.event_codes_to_sampling_percentages_map
                else 100
            )

            error_topics = self.topics.copy()

            if error.debug_details.topic:
                error_topics.add(error.debug_details.topic)

            return ErrorEvent(
                id=str(error.debug_details.id),
                trace_id=self.trace_id,
                code=event_code,
                topics=error_topics if error_topics else None,
                level=EventLevel.ERROR,
                path=self.request_details.path if self.request_details else None,
                method=self.request_details.method if self.request_details else None,
                query_params=self.request_details.query_params if self.request_details else None,
                user_agent=self.request_details.user_agent if self.request_details else None,
                message=error.debug_details.debug_message,
                context_metadata=self.context_metadata if self.context_metadata else None,
                details=error.debug_details.debug_details,
                severity=error.debug_details.severity,
                occurred_while=error.debug_details.occurred_while,
                caused_by=original_error_details,
                status_code=error.public_details.status_code,
                public_code=error.public_details.code,
                public_message=error.public_details.message,
                public_details=error.public_details.details,
                sampling_percentage=sampling_percentage,
                timestamp=datetime.now(tz=timezone.utc).isoformat(),
            ).model_dump(mode="json")

        return {
            "type": type(error).__name__,
            "message": str(error),
            "stack_trace": traceback.format_exception(
                type(error), error, error.__traceback__
            ),
        }


    def _should_log_based_on_sampling_percentage(self, event_code: str) -> bool:
        """
        Determines whether an event should be logged based on its code and the configured sampling percentages.
        """

        if not self.event_codes_to_sampling_percentages_map:
            return True

        sampling_percentage = self.event_codes_to_sampling_percentages_map.get(event_code, 100)

        if sampling_percentage <= 0:
            return False

        if sampling_percentage >= 100:
            return True

        return random.randint(0, 100) < sampling_percentage