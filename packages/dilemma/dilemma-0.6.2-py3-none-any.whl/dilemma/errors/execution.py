from contextlib import contextmanager

from lark.exceptions import VisitError

from .exc import DilemmaError, EvaluationError
from ..logconf import get_logger

log = get_logger(__name__)


@contextmanager
def execution_error_handling(expression: str):
    """
    Context manager for handling common expression evaluation errors
    with consistent error reporting.

    Args:
        expression: The expression being evaluated

    Raises:
        DilemmaError subclasses with templated error messages
    """

    try:
        yield
    except DilemmaError as dilemma_error:
        log.info("Caught early DilemmaError: %s", dilemma_error)
        # If it's already a DilemmaError, just let it propagate
        raise dilemma_error

    except VisitError as e:
        log.info("Caught VisitError %s", e)
        # Extract the original error from VisitError if possible
        if isinstance(e.orig_exc, DilemmaError):
            log.info("Original Error was DilemmaError, re-raising. msg: %s", e)
            raise e.orig_exc

        log.info("Wrapping VisitError in EvaluationError. msg       : %s", e)
        # Otherwise wrap it in EvaluationError
        raise EvaluationError(
            template_key="evaluation_error",
            expression=expression,
            error_type="VisitError",
            details=str(e),
        ) from e

    except Exception as err:
        log.warning("Caught Not VisitError: %s", err)

        errtype = str(type(err))
        raise EvaluationError(
            template_key="evaluation_error",
            expression=expression,
            error_type=errtype,
            details=str(err),
        ) from err
