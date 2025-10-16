"""Example of a custom retry handler.
Retry handler must have the following parameters:

e: Exception
retry_config: dict
-- any custom input
*args
**kwargs

The decorator might be submitting things that your custom handler is not expecting so *args and **kwargs are required

All retry handlers must return an integer which is the delay/sleep time in seconds.
"""

from yet_another_retry import retry


def custom_retry_handler(
    e: Exception, retry_config: dict, sleep_modifier: int, *args, **kwargs
) -> int:
    """Custom handler that accepts the config and any other extra parameters required

    Args:
        e(Exception): the exception raised
        retry_config(dict): the config from the decorator
        sleep_modifier(int): a modifier for the sleep delay

    Returns:
        int: the time to sleep in seconds
    """

    attempt = retry_config["attempt"]
    print(f"This is attempt nr {attempt}")
    print(f"The error was a {e.__name__} Exception")
    delay = attempt * sleep_modifier
    print(f"Will sleep for {delay} seconds")

    return delay


@retry(retry_handler=custom_retry_handler, extra_kwargs={"sleep_modifier": 5})
def my_function():
    raise Exception("This is an exception")


my_function()
