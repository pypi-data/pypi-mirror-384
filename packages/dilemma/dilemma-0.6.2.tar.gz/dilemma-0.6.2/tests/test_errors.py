import pytest

from dilemma.errors import exc
from dilemma.errors.messages import get_default_templates

def test_exc():
    assert exc.DilemmaError.template_key is None
    assert exc.SyntaxError.template_key is not None
    details = "XOG is not a keywor"
    se = exc.SyntaxError(details=details)
    assert details in se.help


def test_excecptions_have_templates():
    templates = get_default_templates()
    for name in dir(exc):
        candidate_exception = getattr(exc, name)
        if type(candidate_exception) is type and  issubclass(candidate_exception, exc.DilemmaError):
            if candidate_exception is not exc.DilemmaError:
                assert candidate_exception.template_key in templates