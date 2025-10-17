from typing import Optional
import logging
import sys


class LoggerSingleton:
    _instance: Optional[logging.Logger] = None

    _LOG_FILE = 'logs/general.log'
    _LOG_FORMAT = (
        '| %(levelname)-11s %(asctime)s | '
        '%(message)s \n'
    )
    _DATE_FORMAT = '%H:%M'

    @classmethod
    def set_logger_state(cls, enable_logs: bool = False) -> None:
        if not enable_logs:
            logging.disable(logging.CRITICAL)

    @classmethod
    def get_logger(cls, name: str = 'GOOGLE_CLIENT') -> logging.Logger:
        """
        Returns the logger singleton instance.
        Only configures the logger for the first call.
        """
        if cls._instance is None:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)

            formatter = logging.Formatter(cls._LOG_FORMAT, cls._DATE_FORMAT)

            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setLevel(logging.ERROR)
            stream_handler.setFormatter(formatter)

            error_handler = logging.StreamHandler(sys.stderr)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)

            logger.addHandler(stream_handler)
            logger.addHandler(error_handler)

            cls._instance = logger

        return cls._instance

def setup_logger(name: str = 'APP_ROOT') -> logging.Logger:
    return LoggerSingleton.get_logger(name)