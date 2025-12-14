from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    if name is None:
        raise ValueError("logger name must not be None.")

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

