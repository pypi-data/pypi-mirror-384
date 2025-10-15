import sys
import logging

from datetime import datetime

from pythonjsonlogger import jsonlogger


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        jsonlogger.JsonFormatter.add_fields(
            self,
            log_record,
            record,
            message_dict
        )

        log_record['name'] = record.name
        log_record['level'] = record.levelname

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        log_record['timestamp'] = now


def setup(
    logger_root,
    level=logging.INFO,
    filename=None,
    log_exception=True,
):
    logger = logging.getLogger(logger_root)
    logger.setLevel(level)

    handler = (
        logging.StreamHandler() if filename is None
        else logging.FileHandler(filename)
    )

    formatter = JsonFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    if log_exception:
        default_hook = sys.excepthook

        def exception_logger(exc_type, exc_value, exc_traceback):
            if not issubclass(exc_type, KeyboardInterrupt):
                logger.error(
                    'Uncaught exception',
                    exc_info=(exc_type, exc_value, exc_traceback)
                )
            default_hook(exc_type, exc_value, exc_traceback)

        sys.excepthook = exception_logger

    return logger
