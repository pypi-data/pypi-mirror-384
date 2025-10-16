import pytest
from yet_another_retry.exception_handlers import default_exception_handler


def test_default_retry_handler():
    try:
        default_exception_handler(e=Exception, retry_config={})
        assert False
    except Exception:
        assert True
