import logging
import re
import sys

SENSITIVE_PATTERNS = [
    re.compile(r'(api[-_]?key\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(authorization\s*[:=]\s*["\']?Bearer\s+)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(bearer\s+)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(password\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(token\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(private[-_]?key\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        for pattern in SENSITIVE_PATTERNS:
            text = pattern.sub(r'\1[REDACTED]', text)
        return text


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("legal_ai")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
