import logging
import sys

from app.core.request_context import get_request_id


LOG_FORMAT = (
    "%(asctime)s "
    "%(levelname)s "
    "request_id=%(request_id)s "
    "logger=%(name)s "
    "message=%(message)s"
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(handler)

    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

        has_request_id_filter = any(
            isinstance(existing_filter, RequestIdFilter)
            for existing_filter in handler.filters
        )

        if not has_request_id_filter:
            handler.addFilter(RequestIdFilter())
