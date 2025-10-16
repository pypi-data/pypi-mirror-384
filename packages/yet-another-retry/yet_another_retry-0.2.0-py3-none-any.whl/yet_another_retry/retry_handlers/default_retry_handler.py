def default_retry_handler(
    e: Exception, retry_config: dict = {}, retry_delay_seconds: int = 0, *args, **kwargs
) -> int:
    """Package default retry handler

    Will return return nr of seconds to sleep

    Args:
        e(Exception): the exception that occured
        retry_config(dict): the retry config from the decorator
        retry_delay_seconds(int): nr of seconds to sleep for between retries. Defaults to 0
    """
    return retry_delay_seconds
