from datetime import datetime, timezone
import json
import logging
import logging.handlers
import queue

from pydantic import BaseModel


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        try:
            if hasattr(record, "event") and isinstance(record.event, BaseModel):
                return record.event.model_dump_json()

            if hasattr(record, "event"):  # Event is a dictionary
                return json.dumps(record.event, ensure_ascii=False)

        except Exception as e:
            return self.serialization_error_log(record, e)

        return json.dumps(
            {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
            }
        )

    def serialization_error_log(self, record: logging.LogRecord, e: Exception) -> str:
        return json.dumps(
            {
                "code": "LOGGER_JSON_SERIALIZATION_ERROR",
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "message": f"Failed to serialize event to JSON: {str(e)}",
            }
        )

def create_json_logger() -> logging.Logger:
    """
    Creates and configures a JSON logger.

    Returns:
        logging.Logger: Configured JSON logger.
    """

    json_event_logger = logging.getLogger("json_logger")

    if not json_event_logger.handlers:
        json_event_logger.setLevel(logging.INFO)
        log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)  # infinite size
        queue_handler = logging.handlers.QueueHandler(log_queue)

        stream_handler = logging.StreamHandler()
        listener = logging.handlers.QueueListener(log_queue, stream_handler)
        stream_handler.setFormatter(JsonFormatter())
        json_event_logger.addHandler(queue_handler)
        json_event_logger.propagate = False

        listener.start()
        json_event_logger.listener = listener  # type: ignore[attr-defined]

    return json_event_logger
