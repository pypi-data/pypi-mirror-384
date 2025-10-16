import logging


def get_logger(name="dilemma"):
    """
    Returns a logger with the specified name, configured for the Dilemma project.
    Ensures consistent formatting and handler setup across the project.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)
    return logger
