import sys

from loguru import logger

from .settings import settings


def setup() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
    )