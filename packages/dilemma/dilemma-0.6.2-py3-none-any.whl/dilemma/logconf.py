import logging


def get_logger(name="dilemma"):
    """
    Returns a logger with the specified name, configured for the Dilemma project.
    Ensures consistent formatting and handler setup across the project.
    """
    logger = logging.getLogger(name)
    # Check if the logger has its own handlers (not inherited from parent)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Always ensure the logger level is set to WARNING
    logger.setLevel(logging.WARNING)
    return logger
