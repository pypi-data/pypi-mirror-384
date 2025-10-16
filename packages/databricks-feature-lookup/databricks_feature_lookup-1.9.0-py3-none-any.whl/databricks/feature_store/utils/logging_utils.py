import logging


def get_logger(name: str, log_level: int = logging.WARNING) -> logging.Logger:
    logger = logging.getLogger(name)
    # A handler needs to be created to config the current logger.
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(log_level)
    # Disable propagation to prevent duplicate logging when root logger has handlers
    logger.propagate = False
    return logger
