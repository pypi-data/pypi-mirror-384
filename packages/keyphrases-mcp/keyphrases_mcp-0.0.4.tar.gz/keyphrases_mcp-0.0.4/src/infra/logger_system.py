import logging
from logging import Logger
import sys
from typing import Callable

from src.infra.logger import LoggerProtocol
from src.config import LOG_LEVEL


class LoggerSystem(LoggerProtocol):
    def __init__(self, logger: Logger):
        self.logger = logger

    def print(self, message: str):
        self.logger.info(message)

    def print_spinner(self, message: str) -> Callable[[str], None]:
        logger = self.logger
        logger.info(message)

        def stop_spinner(message_postfix: str):
            logger.info(message_postfix)

        return stop_spinner


def configure_logging() -> int:
    """Configure logging based on environment.

    - Default level WARNING
    - LOG_LEVEL to override

    Returns the resolved log level. Idempotent.
    """

    level = _resolve_log_level()
    root = logging.getLogger()

    # Always set the root logger level
    root.setLevel(level)

    # Only lower overly-restrictive handler thresholds to avoid host filtering.
    # - Leave NOTSET (0) alone so it defers to logger/root levels
    # - Do not raise handler thresholds (respect host-configured verbosity)
    for h in root.handlers:
        try:
            cur = getattr(h, "level", None)
            if isinstance(cur, int) and cur != logging.NOTSET and cur > level:
                h.setLevel(level)
        except Exception:
            # Log at DEBUG to avoid noisy stderr while still providing diagnostics.
            logging.getLogger(__name__).debug("Failed to adjust handler level for handler %r", h, exc_info=True)

    # Only add our own stderr handler if there are NO handlers at all.
    # Many hosts (pytest, uv, VS Code) install a console handler already.
    if not root.handlers:
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(level)
        sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        root.addHandler(sh)

    # Route warnings.warn(...) through logging
    logging.captureWarnings(True)

    return level


def _resolve_log_level() -> int:
    """Resolve desired log level from LOG_LEVEL.

    Accepts numeric strings or standard level names (DEBUG, INFO, WARNING,
    ERROR, CRITICAL, NOTSET) including aliases WARN and FATAL. Defaults to INFO.
    """
    name = LOG_LEVEL
    if name:
        s = name.strip()
        try:
            return int(s)
        except ValueError:
            pass
        level = getattr(logging, s.upper(), None)
        if isinstance(level, int):
            return level
    return logging.INFO
