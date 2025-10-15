import os
from pathlib import Path
import structlog
import logging

from zenx.settings import Settings

log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def limit_body_length(logger, method_name, event_dict):
    if 'item' in event_dict and isinstance(event_dict['item'], dict):
        item = event_dict['item']
        if 'body' in item and isinstance(item['body'], str):
            max_length = 50
            if len(item['body']) > max_length:
                log_item = item.copy()
                log_item['body'] = log_item['body'][:max_length] + '...'
                event_dict['item'] = log_item
    return event_dict


def configure_logger(name: str, settings: Settings) -> structlog.BoundLogger:
    logging_level = log_levels[settings.LOG_LEVEL]
    
    if settings.APP_ENV == "prod":
        os.makedirs("logs", exist_ok=True)
        file_path = Path("logs", name).with_suffix(".log")
        if file_path.exists():
            file_path.rename(file_path.with_suffix(".log.bak"))
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging_level),
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.add_log_level,
                limit_body_length,
                # format_exc_info suits with JSONRenderer
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.WriteLoggerFactory(
                file=file_path.open("wt")
            ),
        )
    else:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging_level),
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.add_log_level,
                limit_body_length,
                structlog.dev.ConsoleRenderer(sort_keys=False),
            ],
        )
    log: structlog.BoundLogger = structlog.get_logger()
    return log
