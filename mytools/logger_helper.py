import logging
import pathlib

import yaml

BASE = pathlib.Path(__file__).resolve().parents[1]
LOG_ROOT = BASE / "logs"
LOG_ROOT.mkdir(parents=True, exist_ok=True)


def get_job_logger(job_id: str) -> logging.Logger:
    logger_name = f"claim_ai.{job_id}"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler (append)
    file_handler = logging.FileHandler(LOG_ROOT / f"{job_id}.log", mode="a")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also print to stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
