from yet_another_retry.retry_handlers import sleep_attempt_seconds
import random


def test_sleep_attempt_seconds():

    try:
        random_attempt = random.randint(1, 10)
        sleep_seconds = sleep_attempt_seconds(
            e=Exception, retry_config={"attempt": random_attempt}
        )

        assert sleep_seconds == random_attempt
    except:
        assert False
