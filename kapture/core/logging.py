import logging
import sys
from logging.handlers import RotatingFileHandler

from kapture.core.paths import LOGS_DIR

_logger = None


def get_logger(name="kapture"):
    global _logger
    if _logger is not None:
        return _logger
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = RotatingFileHandler(LOGS_DIR / "kapture.log", maxBytes=2_000_000, backupCount=3)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(fh)
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(logging.WARNING)
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(sh)
    _logger = logger
    return logger
