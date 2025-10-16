import pytest
from yet_another_retry.retry_handlers import default_retry_handler


def test_default_retry_handler():

    try:
        delay_seconds = default_retry_handler(e=Exception, retry_config={})

        assert delay_seconds == 0
    except:
        assert False
