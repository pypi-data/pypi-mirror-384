from typing import Optional
from core_infinity_stones.errors.base_error import HttpError, LocalizedMessage, Severity


class ResponseStatusCodeError(HttpError):
    def __init__(
        self,
        url: str,
        status_code: int,
        debug_description: str,
        messages_by_status_codes: Optional[dict[int, str]] = None,
    ):
        message = (
            messages_by_status_codes.get(status_code, "")
            if messages_by_status_codes and status_code in messages_by_status_codes
            else "An error occurred while processing the request."
        )

        super().__init__(
            status_code=status_code,
            severity=Severity.MEDIUM if 400 <= status_code < 500 else Severity.HIGH,
            code="RESPONSE_STATUS_CODE_ERROR",
            message=LocalizedMessage(en=message, ar=message),
            debug_message=debug_description,
            debug_details={"url": url, "status_code": status_code},
        )
