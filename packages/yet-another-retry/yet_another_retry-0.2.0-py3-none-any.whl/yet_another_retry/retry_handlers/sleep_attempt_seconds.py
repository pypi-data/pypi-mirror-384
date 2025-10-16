def sleep_attempt_seconds(
    e: Exception, retry_config: dict = {}, *args, **kwargs
) -> int:
    """Retry handler that returns the attempt number as delay

    Will return return nr of seconds to sleep

    Args:
        e(Exception): the exception that occured
        retry_config(dict): the retry config from the decorator
    """

    retry_delay_seconds = retry_config["attempt"]

    return retry_delay_seconds
