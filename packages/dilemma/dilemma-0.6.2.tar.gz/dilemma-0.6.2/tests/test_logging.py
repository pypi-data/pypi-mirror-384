import logging

from dilemma.logconf import get_logger


def test_get_logger():
    """Test the get_logger function to ensure it returns a logger instance."""

    # Use a unique logger name to avoid conflicts between test runs
    import uuid

    unique_name = f"test_logger_{uuid.uuid4().hex[:8]}"

    test_logger = logging.getLogger(unique_name)
    assert test_logger.handlers == []
    logger = get_logger(unique_name)
    assert logger is test_logger
    assert logger.name == unique_name
    assert logger.level == logging.WARNING
    assert len(logger.handlers) > 0
